# Pros
- Very quick and easy to set up end points
- Auto generated docs
	- Creating schemas for this is done inside code and is very easy
- Python ecosystem
- Easy to deploy
# Cons
- Python performance
- Lacks convention and opinions
	- Code could become messy over time as different people contribute in different styles
	- May need to make our own programming style sheet
- Doesn't offer many security cosntructs (only OAuth2)
- Weak typing can get very messy

# Final Thoughts
Could be a good option as a separate microservice API that runs the solver. May not be the best option as our primary API since it does not offer a lot of high level constructs, much of the creation and management of those features will be up to us.

This is probably an appropriate choice if our deployment is limited entirely to the University setting. If this were deployed as an app where multiple universities or other education providers wanted to use it a that the same time (in a similar manner to Canvas), this framework probably would not scale well enough.