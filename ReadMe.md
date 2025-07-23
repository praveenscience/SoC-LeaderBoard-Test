# SoC LeaderBoard Playground Repo

![Testing Completed! Thanks for being a part of this!](https://i.imgur.com/SA51k7v.png)

We want the base Label to be: `SoCTest25`. Only these PRs will be considered.

We have level labels too:

* `Beginner`: `5` Points
* `Intermediate`: `10` Points
* `Advanced`: `20` Points

Create a couple of files in this repo and submit the PRs here.

Use Cases:

* Since it's based on the Projects, it only looks at the list of projects given. ✅
* Should not consider the users that are not configured. ✅
* Should not consider the PRs that don't have the base class even though user is there. ✅
* Should consider the lowest level (or highest), whichever configured first if there are multiple. ❎ (This one is flaky, not sure about the output! But it's alright!)
* Unmerged valid PRs should be not considered too. ✅

PR Check: https://api.github.com/repos/praveenscience/SoC-LeaderBoard-Test/pulls/PR_ID

Let's test this out!
