Just make it hidden here!

```javascript
/**
 * PR Score Calculator using GitHub GraphQL API
 *
 * This script fetches PRs from specified GitHub repositories based on labels,
 * calculates scores for users, and saves results to a JSON file.
 */

const axios = require("axios");
const fs = require("fs");
const path = require("path");

// Define variables for projects, users, and labels
const projects = [{ owner: "praveenscience", repo: "SoC-LeaderBoard-Test" }];

const users = ["setco-website", "hellomanishahere", "PrathibhaS"];

const baseLabel = "SoCTest25";
const levelLabels = {
  Beginner: 5,
  Intermediate: 10,
  Advanced: 20
};

// GitHub Personal Access Tokens for rotation
const githubTokens = [
  process.env.GITHUB_TOKEN_1 || "",
  process.env.GITHUB_TOKEN_2 || "",
  process.env.GITHUB_TOKEN_3 || ""
];
let currentTokenIndex = 0;

// Get next token in round-robin fashion
function getNextToken() {
  const token = githubTokens[currentTokenIndex];
  currentTokenIndex = (currentTokenIndex + 1) % githubTokens.length;
  return token;
}

/**
 * Execute GraphQL query against GitHub API
 */
async function executeGraphQLQuery(query, variables) {
  const token = getNextToken();

  try {
    console.log(`Using token ending with ...${token.slice(-4)}`);

    const response = await axios({
      url: "https://api.github.com/graphql",
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      data: {
        query,
        variables
      }
    });

    // Check for errors in the response
    if (response.data.errors) {
      console.error("GraphQL Errors:", response.data.errors);
      throw new Error(`GraphQL Error: ${response.data.errors[0].message}`);
    }

    return response.data;
  } catch (error) {
    console.error("Request Error:", error.message);
    if (error.response) {
      console.error("Status:", error.response.status);
      console.error("Response:", error.response.data);
    }
    throw error;
  }
}

/**
 * Fetch all PRs from a repository with pagination
 */
async function fetchAllPRs(owner, repo) {
  const query = `
    query($owner: String!, $repo: String!, $labels: [String!], $cursor: String) {
      repository(owner: $owner, name: $repo) {
        pullRequests(first: 100, states: [MERGED], labels: $labels, after: $cursor) {
          nodes {
            number
            title
            url
            state
            createdAt
            mergedAt
            author {
              login
            }
            labels(first: 10) {
              nodes {
                name
              }
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
      rateLimit {
        limit
        remaining
        resetAt
      }
    }
  `;

  const allPRs = [];
  let hasNextPage = true;
  let cursor = null;

  console.log(`\nFetching PRs for ${owner}/${repo} with label ${baseLabel}...`);

  while (hasNextPage) {
    const variables = {
      owner,
      repo,
      labels: [baseLabel],
      cursor
    };

    try {
      console.log(`Fetching page of PRs${cursor ? " with cursor" : ""}...`);
      const result = await executeGraphQLQuery(query, variables);

      // Log rate limit information
      const rateLimit = result.data.rateLimit;
      console.log(
        `Rate limit: ${rateLimit.remaining}/${
          rateLimit.limit
        } (resets at ${new Date(rateLimit.resetAt).toLocaleTimeString()})`
      );

      const pullRequests = result.data.repository.pullRequests;
      console.log(`Retrieved ${pullRequests.nodes.length} PRs in this page`);

      allPRs.push(...pullRequests.nodes);

      hasNextPage = pullRequests.pageInfo.hasNextPage;
      cursor = pullRequests.pageInfo.endCursor;

      // Add a delay to be nice to the API
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      // If we hit an error, wait longer and try with the next token
      console.error(
        `Error fetching page. Waiting 5 seconds before trying again...`
      );
      await new Promise(resolve => setTimeout(resolve, 5000));
      // Don't update the cursor so we retry the same page
    }
  }

  console.log(`Total PRs fetched for ${owner}/${repo}: ${allPRs.length}`);
  return allPRs;
}

/**
 * Check if a PR qualifies based on our criteria and calculate its score
 */
function evaluatePR(pr, targetUsers) {
  // Skip if author isn't in our target users list
  const author = pr.author ? pr.author.login : null;
  if (!author || !targetUsers.includes(author)) {
    return null;
  }

  // Extract labels
  const labels = pr.labels.nodes.map(node => node.name);

  // Find level label and corresponding score
  let level = null;
  let score = 0;

  for (const levelLabel in levelLabels) {
    if (labels.includes(levelLabel)) {
      level = levelLabel;
      score = levelLabels[levelLabel];
      break;
    }
  }

  // Skip if no valid level label found
  if (!level) {
    return null;
  }

  return {
    number: pr.number,
    title: pr.title,
    url: pr.url,
    state: pr.state,
    createdAt: pr.createdAt,
    mergedAt: pr.mergedAt,
    author: author,
    labels: labels,
    level: level,
    score: score
  };
}

/**
 * Main function to run the script
 */
async function main() {
  // Initialize results structure
  const results = {
    timestamp: new Date().toISOString(),
    summary: {
      totalPRs: 0,
      totalPoints: 0
    },
    users: {},
    projects: {},
    prs: []
  };

  // Initialize user data
  users.forEach(user => {
    results.users[user] = {
      totalScore: 0,
      prCount: 0,
      prsByLevel: Object.keys(levelLabels).reduce((acc, level) => {
        acc[level] = 0;
        return acc;
      }, {})
    };
  });

  // Process each project
  for (const { owner, repo } of projects) {
    const projectKey = `${owner}/${repo}`;
    results.projects[projectKey] = {
      totalPRs: 0,
      prsByUser: users.reduce((acc, user) => {
        acc[user] = 0;
        return acc;
      }, {})
    };

    try {
      // Fetch all PRs for the current project
      const allPRs = await fetchAllPRs(owner, repo);

      // Process each PR
      for (const pr of allPRs) {
        const evaluatedPR = evaluatePR(pr, users);

        if (evaluatedPR) {
          // Add project info to PR
          evaluatedPR.project = projectKey;

          // Update user stats
          const user = evaluatedPR.author;
          const level = evaluatedPR.level;
          const score = evaluatedPR.score;

          results.users[user].totalScore += score;
          results.users[user].prCount++;
          results.users[user].prsByLevel[level]++;

          // Update project stats
          results.projects[projectKey].totalPRs++;
          results.projects[projectKey].prsByUser[user]++;

          // Update global stats
          results.summary.totalPRs++;
          results.summary.totalPoints += score;

          // Add PR to the list
          results.prs.push(evaluatedPR);

          console.log(
            `Qualifying PR: #${pr.number} by ${user} in ${projectKey} - ${level} (${score} points)`
          );
        }
      }
    } catch (error) {
      console.error(`Error processing ${projectKey}:`, error.message);
    }
  }

  // Display summary
  console.log("\n===== SUMMARY =====");
  console.log(`Total qualifying PRs: ${results.summary.totalPRs}`);
  console.log(`Total points awarded: ${results.summary.totalPoints}`);

  console.log("\n===== USER SCORES =====");
  for (const user in results.users) {
    const userData = results.users[user];
    if (userData.prCount > 0) {
      console.log(
        `${user}: ${userData.totalScore} points (${userData.prCount} PRs)`
      );
      for (const level in userData.prsByLevel) {
        if (userData.prsByLevel[level] > 0) {
          console.log(`  - ${level}: ${userData.prsByLevel[level]} PRs`);
        }
      }
    } else {
      console.log(`${user}: No qualifying PRs`);
    }
  }

  // Save results to JSON file
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `pr-scores-${timestamp}.json`;

  fs.writeFileSync(
    path.join(__dirname, filename),
    JSON.stringify(results, null, 2)
  );

  console.log(`\nResults saved to ${filename}`);
}

// Execute the main function
main().catch(error => {
  console.error("Fatal error:", error.message);
});
```
