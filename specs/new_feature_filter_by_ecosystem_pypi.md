can we add another option to find all dependencies based on ecosystem

The API to use for this is :
https://semgrep.dev/api/v1/deployments/{deploymentId}/dependencies

Request Body schema: application/json

We will use the following filters
{
  "dependencyFilter": {
    "ecosystem": "pypi"
  }
}

![alt text](image-3.png)

We will generate a XLSX file: one for licences for ecosystem: pypi 

This is in addition to the existing ouput

if user wants XLSX file for ecoystsem: pypi, they should set an environment variable SEMGREP_ECOSYSTEM_PYPI to true in .env file

