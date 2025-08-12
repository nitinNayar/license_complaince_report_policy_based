lets work on a new feature

currently we have the repository_id. this is not very user friendly.
I would like to query the repository_name from the repository_id and add this as an attribute to the dependendy object
also when we write this to XLS, we should add the repository name

to get a list of all repositories and their ids, we can use the following Semgrep API endpoint: https://semgrep.dev/api/v1/deployments/{deployment_slug}/projects
NOTE: this now requires the user to give us a new input- deployment_slug
We should expect this to come from the .env file as well like the deployment_id

Sample API response for this API request is given below:
{
  "projects": [
    {
      "created_at": "2020-11-18 23:28:12.391807",
      "default_branch": "refs/heads/main",
      "id": 1234567,
      "latest_scan_at": "2023-01-13T20:51:51.449081Z",
      "name": "returntocorp/semgrep",
      "primary_branch": "refs/heads/custom-main",
      "tags": [
        "tag"
      ],
      "url": "https://github.com/returntocorp/semgrep"
    }
  ]
}

