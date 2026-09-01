"""
To run this script:
    uv run python -m scripts.seed
while backend is working directly
"""

import random
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import httpx
from faker import Faker

from src.constants import UNIT_ROLE_ADMINISTRATOR, USER_ROLE_COORDINATOR, USER_ROLE_STUDENT

BASE_URL = "http://localhost:8000"
PASSWORD = "Password123"
MAX_WORKERS = 8

STUDENTS_PER_UNIT = 50
ADMINS_PER_UNIT = 2
MIN_GROUP_SIZE = 4
MAX_GROUP_SIZE = 5
MAX_NEW_STUDENTS = 1
NEW_STUDENT_CHANCE = 0.25

# (number of groups, members each, whether members share any free time)
GROUP_PLAN = [
    (5, 5, True),     # full and cohesive
    (2, 4, True),     # at the minimum size
    (2, 5, False),    # full but nobody shares a slot
    (1, 3, True),     # short of min_group_size
]

# Weekdays 09:00-17:00 for the constrained unit; the other offers all 168 slots
BUSINESS_HOURS = [
    f"{day}{hour:02d}"
    for day in ("monday", "tuesday", "wednesday", "thursday", "friday")
    for hour in range(9, 18)
]

DELIVERY_MODES = ["internal", "external", "online"]
SKILLS = [
    "Python", "JavaScript", "React", "SQL", "Figma", "UX research", "Testing",
    "DevOps", "Java", "C#", "Data analysis", "Technical writing", "Project planning",
]

GROUPED_STUDENTS = sum(count * size for count, size, _ in GROUP_PLAN)
assert GROUPED_STUDENTS <= STUDENTS_PER_UNIT, (
    f"GROUP_PLAN needs {GROUPED_STUDENTS} students but STUDENTS_PER_UNIT is {STUDENTS_PER_UNIT}"
)

rng = random.Random(2026)
fake = Faker("en_AU")
Faker.seed(2026)
run_id = int(time.time()) % 100000

# httpx.Client is thread safe, so one shared client serves every worker
client = httpx.Client(base_url=BASE_URL, timeout=60)

# Deliberately unseeded: emails have to differ between runs or the second run
# collides with users the first one already registered.
email_rng = random.Random()
_issued_emails = set()


def unique_email():
    while True:
        email = f"test-user{email_rng.randint(1, 99_999_999)}@test.com"
        if email not in _issued_emails:
            _issued_emails.add(email)
            return email


def parallel(fn, items):
    """Runs fn over items concurrently, preserving order."""
    if not items:
        return []

    results: list = [None] * len(items)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fn, item): index for index, item in enumerate(items)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


@dataclass
class Member:
    """One seeded account, and which group it belongs in once groups exist."""
    slots: list[str]
    role: str = USER_ROLE_STUDENT
    group_index: int | None = None
    is_admin: bool = False
    user_id: int = 0
    headers: dict = field(default_factory=dict)
    email: str = ""


def register_and_login(member):
    member.email = unique_email()
    body = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": member.email,
        "password": PASSWORD,
        "role": member.role,
    }
    r = client.post("/auth/register", json=body)
    assert r.status_code == 200, r.text
    member.user_id = r.json()["id"]

    r = client.post("/auth/login", json={"email": member.email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    member.headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return member


def cohesive_slots(offered, shared):
    """Shared core plus a few extras, so the group has a genuine intersection."""
    extras = rng.sample([s for s in offered if s not in shared], rng.randint(2, 6))
    return sorted(set(shared) | set(extras))


def scattered_slots(offered, member_index, member_count):
    """Each member draws from their own slice, so the intersection is empty."""
    chunk = len(offered) // member_count
    pool = offered[member_index * chunk:(member_index + 1) * chunk]
    return sorted(rng.sample(pool, min(len(pool), rng.randint(2, 4))))


class UnitSeeder:
    def __init__(self, name, constrained):
        self.name = name
        self.constrained = constrained
        self.members: list[Member] = []
        self.groups: list[dict] = []

    # --- phase 1 -------------------------------------------------------------
    def create_unit(self):
        self.coordinator = register_and_login(Member(slots=[], role=USER_ROLE_COORDINATOR))

        body = {"name": self.name, "min_group_size": MIN_GROUP_SIZE, "max_group_size": MAX_GROUP_SIZE}
        if self.constrained:
            body["max_new_students"] = MAX_NEW_STUDENTS
            body["time_slots"] = BUSINESS_HOURS

        r = client.post("/units/create", json=body, headers=self.coordinator.headers)
        assert r.status_code == 201, r.text
        self.unit = r.json()
        self.slots = self.unit["time_slots"]

    def plan_members(self):
        """Decides every account and its availability before anything is created."""
        for _ in range(ADMINS_PER_UNIT):
            self.members.append(Member(slots=rng.sample(self.slots, 6), is_admin=True))

        group_index = 0
        for count, size, cohesive in GROUP_PLAN:
            for _ in range(count):
                shared = rng.sample(self.slots, rng.randint(1, 3))
                for position in range(size):
                    slots = cohesive_slots(self.slots, shared) if cohesive else scattered_slots(self.slots, position, size)
                    self.members.append(Member(slots=slots, group_index=group_index))
                group_index += 1

        ungrouped = [
            Member(slots=sorted(rng.sample(self.slots, rng.randint(3, 8))))
            for _ in range(STUDENTS_PER_UNIT - GROUPED_STUDENTS)
        ]
        assert ungrouped, "GROUP_PLAN uses every student, leaving nobody outside a group"
        self.members.extend(ungrouped)

        # One known account with no group, so it can be signed into for testing
        self.ungrouped = ungrouped[0]
        self.group_count = group_index

    # --- phase 2 -------------------------------------------------------------
    def enrol_member(self, member):
        r = client.post("/units/join", json={"code": self.unit["code"]}, headers=member.headers)
        assert r.status_code == 200, r.text

        body = {
            "time_preferences": member.slots,
            "is_new_student": rng.random() < NEW_STUDENT_CHANCE,
            "delivery_mode": rng.choice(DELIVERY_MODES),
            "skills": ", ".join(rng.sample(SKILLS, rng.randint(1, 3))),
        }
        r = client.patch(f"/units/{self.unit['id']}/me", json=body, headers=member.headers)
        assert r.status_code == 200, r.text

        if member.is_admin:
            r = client.patch(
                f"/units/{self.unit['id']}/members/{member.user_id}",
                json={"role": UNIT_ROLE_ADMINISTRATOR},
                headers=self.coordinator.headers,
            )
            assert r.status_code == 200, r.text
        return member

    # --- phase 3 -------------------------------------------------------------
    def open_group(self, group_index):
        creator = next(m for m in self.members if m.group_index == group_index)
        r = client.post(
            "/groups/create",
            json={"unit_id": self.unit["id"], "is_public": rng.random() < 0.75},
            headers=creator.headers,
        )
        assert r.status_code == 200, r.text
        return r.json()

    # --- phase 4 -------------------------------------------------------------
    def fill_group(self, group_index):
        """Joins are serial within a group so the capacity check can't race."""
        code = self.groups[group_index]["preference_code"]
        joiners = [m for m in self.members if m.group_index == group_index][1:]
        for member in joiners:
            r = client.post("/groups/join", json={"preference_code": code}, headers=member.headers)
            assert r.status_code == 200, r.text
        return len(joiners)

    def report(self):
        r = client.get(f"/groups/{self.unit['id']}", headers=self.coordinator.headers)
        assert r.status_code == 200, r.text
        statuses = Counter(g["status"] for g in r.json())

        print(f"\n{self.name}")
        print(f"  unit id / code   : {self.unit['id']} / {self.unit['code']}")
        print(f"  group sizes      : min {self.unit['min_group_size']}, max {self.unit['max_group_size']}")
        print(f"  max new students : {self.unit['max_new_students']}")
        print(f"  time slots        : {len(self.slots)}")
        print(f"  groups           : {dict(statuses)}")
        print(f"  coordinator      : {self.coordinator.email}")
        print(f"  student, no group: {self.ungrouped.email}")


def main():
    r = client.get("/health")
    assert r.status_code == 200, "dev server is not responding at " + BASE_URL

    seeders = [
        UnitSeeder(f"IFB398 Constrained ({run_id})", constrained=True),
        UnitSeeder(f"IFB399 Unconstrained ({run_id})", constrained=False),
    ]

    for seeder in seeders:
        seeder.create_unit()
        seeder.plan_members()

    parallel(register_and_login, [m for seeder in seeders for m in seeder.members])

    for seeder in seeders:
        parallel(seeder.enrol_member, seeder.members)

    for seeder in seeders:
        seeder.groups = parallel(seeder.open_group, range(seeder.group_count))

    for seeder in seeders:
        parallel(seeder.fill_group, range(seeder.group_count))

    for seeder in seeders:
        seeder.report()

    print(f"\nevery account uses the password {PASSWORD}")


if __name__ == "__main__":
    main()
