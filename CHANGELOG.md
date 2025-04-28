# Changelog

## [0.9.1](https://github.com/pscedu/cpra.mp.management/compare/v0.9.0...v0.9.1) (2025-04-28)


### Bug Fixes

* change clickup_id to int ([8ca87cc](https://github.com/pscedu/cpra.mp.management/commit/8ca87cc11b2d4b170b72eeecea3986aaf32cb584))

## [0.9.0](https://github.com/pscedu/cpra.mp.management/compare/v0.8.1...v0.9.0) (2025-04-21)


### Bug Fixes

* Adjust comment creation for tasks and add getComments flag for get task endpoints ([4c02287](https://github.com/pscedu/cpra.mp.management/commit/4c022875e07f23800829ab675a21a94846a71c7e))
* Check to make sure that the attribute acutually contains something ([a961ff0](https://github.com/pscedu/cpra.mp.management/commit/a961ff0ac3a01d21090db5f071a5a12e0fa106fd))
* return empty dicts or lists if None ([f040190](https://github.com/pscedu/cpra.mp.management/commit/f040190ef6a138e0a63a4f02875a86e646bad0d7))
* Slight mods for bulk sim run gets ([dd0ee6f](https://github.com/pscedu/cpra.mp.management/commit/dd0ee6f430c4b4f2d2f3fd63ced3f4ce860f47d8))

## [0.8.1](https://github.com/pscedu/cpra.mp.management/compare/v0.8.0...v0.8.1) (2025-04-14)


### Bug Fixes

* change task_id from int to str ([c425700](https://github.com/pscedu/cpra.mp.management/commit/c425700c393052c903064420a725bfe6885d483e))

## [0.8.0](https://github.com/pscedu/cpra.mp.management/compare/v0.7.0...v0.8.0) (2025-04-10)


### Bug Fixes

* syntax fix ([164be94](https://github.com/pscedu/cpra.mp.management/commit/164be94225ad027ec7d7854c4ceccf8131a92c9d))

## [0.7.0](https://github.com/pscedu/cpra.mp.management/compare/v0.6.2...v0.7.0) (2025-04-02)


### Features

* enable CORS middleware ([06efc7b](https://github.com/pscedu/cpra.mp.management/commit/06efc7bf1793dd92d201cb209156e5206844720a))
* **login:** read refresh token from Authorization header ([b4c8c69](https://github.com/pscedu/cpra.mp.management/commit/b4c8c69ebe9f889838a50fa5d4a6f7681ceb6b99))
* **response:** add ClickUp ID to user response model ([ccc0e88](https://github.com/pscedu/cpra.mp.management/commit/ccc0e88cd35ae41a118dd11b7f501177a92a66a4))
* **response:** use camel case in response models ([e8fac2e](https://github.com/pscedu/cpra.mp.management/commit/e8fac2e58ba2eea1b7837b117ba1293aa9cbca40))
* **settings:** make CORS origins a setting ([f839239](https://github.com/pscedu/cpra.mp.management/commit/f83923901b0f5833c82efbb3f117075ac2f52353))


### Bug Fixes

* **tokens:** remove user info claims from access token ([3ef33a5](https://github.com/pscedu/cpra.mp.management/commit/3ef33a58a1f79d39542c5a540dc25d591739986c))

## [0.6.2](https://github.com/pscedu/cpra.mp.management/compare/v0.6.1...v0.6.2) (2025-02-26)


### Bug Fixes

* Make sure to include clickup_data in the response ([5c04847](https://github.com/pscedu/cpra.mp.management/commit/5c0484785902c2758c15d76d207ab3024622b49a))
* Only allow status to be updated ([ec769d1](https://github.com/pscedu/cpra.mp.management/commit/ec769d1c57bb4c6bd532d33e6880429c8ee2ad6c))

## [0.6.1](https://github.com/pscedu/cpra.mp.management/compare/v0.6.0...v0.6.1) (2025-02-26)


### Bug Fixes

* Make sure to include clickup_data in the response ([cb95069](https://github.com/pscedu/cpra.mp.management/commit/cb95069c8d2c505c845718a40569ef7a0f1dd388))

## [0.6.0](https://github.com/pscedu/cpra.mp.management/compare/v0.5.1...v0.6.0) (2025-02-26)


### Features

* Support for Simulation Runs ([c3550db](https://github.com/pscedu/cpra.mp.management/commit/c3550dbc32f6a9207849e799ce0110dc081253d0))

## [0.5.1](https://github.com/pscedu/cpra.mp.management/compare/v0.5.0...v0.5.1) (2025-02-19)


### Bug Fixes

* update root path to match callback URLs ([37559f2](https://github.com/pscedu/cpra.mp.management/commit/37559f2b8a503dbe32bcfad9da8b2941e708c206))

## [0.5.0](https://github.com/pscedu/cpra.mp.management/compare/v0.4.0...v0.5.0) (2025-02-05)


### Features

* **clickup:** use query parameter passthrough instead of cookie ([6707193](https://github.com/pscedu/cpra.mp.management/commit/67071938a1392dc6727b3571c5ce63b935befc22))

## [0.4.0](https://github.com/pscedu/cpra.mp.management/compare/v0.3.0...v0.4.0) (2025-01-30)


### Bug Fixes

* don't allow users to update their own role. ([ebc2684](https://github.com/pscedu/cpra.mp.management/commit/ebc26842c0f2d28c4fb878317c15e2c12e8248cd))
* email cannot be updated ([dad8010](https://github.com/pscedu/cpra.mp.management/commit/dad801061c29f3f4a0179fcdcb7ebc26b571ddd4))

## [0.3.0](https://github.com/pscedu/cpra.mp.management/compare/v0.2.3...v0.3.0) (2025-01-13)


### Bug Fixes

* expose 5000 not 8001 ([ab61661](https://github.com/pscedu/cpra.mp.management/commit/ab616614e0059eb9cc3397517c3b0f130f09ddc0))

## [0.2.3](https://github.com/pscedu/cpra.mp.management/compare/v0.2.2...v0.2.3) (2025-01-10)


### Bug Fixes

* Remove psycopg2 ([6385e3f](https://github.com/pscedu/cpra.mp.management/commit/6385e3f4df4d1fd8e31fc4577654e292c023d5e7))

## [0.2.2](https://github.com/pscedu/cpra.mp.management/compare/v0.2.1...v0.2.2) (2025-01-10)


### Bug Fixes

* Add psycopg2-binary to requirements ([f988b36](https://github.com/pscedu/cpra.mp.management/commit/f988b36cf9f342e9442fb4dbc50376feaccb34e8))

## [0.2.1](https://github.com/pscedu/cpra.mp.management/compare/v0.2.0...v0.2.1) (2025-01-10)


### Bug Fixes

* Add psycopg2 to requirements ([5fa24fd](https://github.com/pscedu/cpra.mp.management/commit/5fa24fd05e92f14fa0f84ea2d7b9bbaac6373a31))

## [0.2.0](https://github.com/pscedu/cpra.mp.management/compare/v0.1.5...v0.2.0) (2025-01-10)


### Features

* Fix up routes and add functionality for connecting to a DB for storing user information. ([1e25490](https://github.com/pscedu/cpra.mp.management/commit/1e25490d8b7fba67b2a9a79d98af80b9b6f89c4f))
* Fix up routes and add functionality for connecting to a DB for storing user information. ([e00c06d](https://github.com/pscedu/cpra.mp.management/commit/e00c06d4754067bab17ba7fafc701b23fffcfcbc))

## [0.1.5](https://github.com/pscedu/cpra.mp.management/compare/v0.1.4...v0.1.5) (2024-12-13)


### Bug Fixes

* **General:** Update requirements.txt ([5b56cc6](https://github.com/pscedu/cpra.mp.management/commit/5b56cc644a88ae5c1f8001cebab1102876e9cc89))

## [0.1.4](https://github.com/pscedu/cpra.mp.management/compare/v0.1.3...v0.1.4) (2024-12-13)


### Features

* **Auth:** Add support for CILogon ([6c81749](https://github.com/pscedu/cpra.mp.management/commit/6c81749b98e585475aeaa27ae46d776a26fc25bb))


### Bug Fixes

* **General:** Formatting ([84a2ef3](https://github.com/pscedu/cpra.mp.management/commit/84a2ef394a5be551826828495f8019619056be25))
* **General:** Formatting ([1bedd26](https://github.com/pscedu/cpra.mp.management/commit/1bedd261384129fc4b27bd40df407098e5a9662f))
* **General:** Syntax updates ([059417c](https://github.com/pscedu/cpra.mp.management/commit/059417cac9b4344045c09244215ce2e645f28021))
* **General:** Update .gitignore ([bb82f5d](https://github.com/pscedu/cpra.mp.management/commit/bb82f5da5fb93935d35869128ca6a93f93faa49a))

## [0.1.3](https://github.com/pscedu/cpra.mp.management/compare/v0.1.2...v0.1.3) (2024-11-18)


### Bug Fixes

* **General:** Add main.py ([b35282e](https://github.com/pscedu/cpra.mp.management/commit/b35282edccb90a666d41b3ead0da9e781b70f0ce))

## [0.1.2](https://github.com/pscedu/cpra.mp.management/compare/v0.1.1...v0.1.2) (2024-11-15)


### Bug Fixes

* **GitHub Workflow:** Remove Python Release ([2c9c03c](https://github.com/pscedu/cpra.mp.management/commit/2c9c03c0ec440fe483659cd7e22931a4a5304d37))
* **Workflow:** Remove with ([9e7baf0](https://github.com/pscedu/cpra.mp.management/commit/9e7baf08af0feaa4ff9885e4aba45b18e75a13fd))

## [0.1.1](https://github.com/pscedu/cpra.mp.management/compare/v0.1.0...v0.1.1) (2024-11-14)


### Bug Fixes

* **Dockerfile:** Fix requirements.txt ([ea8c5e2](https://github.com/pscedu/cpra.mp.management/commit/ea8c5e22fef1487825e5275e67207261d12b1652))

## 0.1.0 (2024-11-14)


### Bug Fixes

* Update README slightly ([cffdfff](https://github.com/pscedu/cpra.mp.management/commit/cffdffffe2c9699c9ad21388ab5f2609e958163c))
