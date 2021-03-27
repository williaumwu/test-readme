**Description**

  - This stack preforms continuous integration through a dockerhost on AWS - ec2.  
  - It responds to webhooks and builds code accordingly.

**Infrastructure**

  - expects a dockerhost be available to be used for builds
  - expects ec2 ecr to be created

**Required**

| argument      | description                            | var type | default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| docker_host   | name of the dockerhost                 | string   | None         |
| repo_url      | the repository to build code from      | string   | None         |

**Optional**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| triggered_branches | branches to trigger builds from        | string   | master       |
| repo_branch        | branch to build from (array)           | array    | master       |

**Sample entry:**

```
build:
  ci_example:
    dependencies: 
      - infrastructure::dockerhost
      - infrastructure::ecr_repo
    stack_name: elasticdev:::ec2_ci
    arguments:
      docker_host: docker_flask_sample
      repo_url: https://github.com/bill12252016/flask_sample
      repo_branch: master
      triggered_branches:
        - master

```






