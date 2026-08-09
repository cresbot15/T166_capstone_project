// Mocked student directory data. No backend endpoint exists to list a unit's
// students with degree/skills/group-completion status (see design spec
// docs/superpowers/specs/2026-08-08-frontend-ui-rework-design.md, Non-goals).
// Replace this module with a real API call once that endpoint exists.

export interface MockStudent {
	id: number;
	name: string;
	degree: string;
	skills: string;
	status: 'complete' | 'incomplete' | 'pending';
	email: string;
}

export const mockStudents: MockStudent[] = [
	{
		id: 1,
		name: 'Isabelle Dayman',
		degree: 'Computer Science',
		skills: 'React, Figma',
		status: 'complete',
		email: 'isabelle.dayman@example.com'
	},
	{
		id: 2,
		name: 'George Grigman',
		degree: 'Computer Science',
		skills: 'Python, SQL',
		status: 'pending',
		email: 'george.grigman@example.com'
	},
	{
		id: 3,
		name: 'Johnny Davis',
		degree: 'Information Systems',
		skills: 'Java',
		status: 'incomplete',
		email: 'johnny.davis@example.com'
	},
	{
		id: 4,
		name: 'Leila Crickey',
		degree: 'Computer Science',
		skills: 'UI Design',
		status: 'complete',
		email: 'leila.crickey@example.com'
	},
	{
		id: 5,
		name: 'Frida Columbus',
		degree: 'Information Technology',
		skills: 'Node.js',
		status: 'pending',
		email: 'frida.columbus@example.com'
	}
];
