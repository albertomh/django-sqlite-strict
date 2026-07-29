# Changelog

## [0.3.0](https://github.com/albertomh/django-sqlite-strict/compare/0.2.0...0.3.0) (2026-07-29)


### Features

* Extend model check to exclude swapped models ([#26](https://github.com/albertomh/django-sqlite-strict/issues/26)) ([460471f](https://github.com/albertomh/django-sqlite-strict/commit/460471f602ad909457f424a1e5142e3b6536c92c))
* Override type mappings rejected by SQLite STRICT ([#28](https://github.com/albertomh/django-sqlite-strict/issues/28)) ([47e904a](https://github.com/albertomh/django-sqlite-strict/commit/47e904add5e769da394627ed4d8675769c79a43c))
* Warning logged when DecimalField with &gt; 15 digits used ([#30](https://github.com/albertomh/django-sqlite-strict/issues/30)) ([eee2f33](https://github.com/albertomh/django-sqlite-strict/commit/eee2f3300ce89c9c3831b6c31b717b61d3709d62))

## [0.2.0](https://github.com/albertomh/django-sqlite-strict/compare/0.1.0...0.2.0) (2026-07-26)


### Features

* Run column types check on AppConfig.ready ([#23](https://github.com/albertomh/django-sqlite-strict/issues/23)) ([bd0f932](https://github.com/albertomh/django-sqlite-strict/commit/bd0f93264e7be77ec689421b8eb470182aac9cbb))


### Bug Fixes

* Check all databases when databases=None ([#19](https://github.com/albertomh/django-sqlite-strict/issues/19)) ([e141b4e](https://github.com/albertomh/django-sqlite-strict/commit/e141b4e94ee2c5a010808bad104c80792b24e729))


### Documentation

* Flesh out README - install, features, development ([#21](https://github.com/albertomh/django-sqlite-strict/issues/21)) ([e36efa6](https://github.com/albertomh/django-sqlite-strict/commit/e36efa689ef6109fd39d28b53d47fb7df110324d))

## 0.1.0 (2026-07-24)


### Features

* Add a strict SchemaEditor that amends CREATE TABLE statements ([#14](https://github.com/albertomh/django-sqlite-strict/issues/14)) ([dd58ab0](https://github.com/albertomh/django-sqlite-strict/commit/dd58ab0ba86382f127da982b5097eeb453c7995a))
* Add AppConfig entrypoint ([#6](https://github.com/albertomh/django-sqlite-strict/issues/6)) ([d3fb77f](https://github.com/albertomh/django-sqlite-strict/commit/d3fb77faf5d9c0654979714f7538cb8c6aa25660))
* Add pyproject.toml and src & tests directories ([#4](https://github.com/albertomh/django-sqlite-strict/issues/4)) ([529ef1c](https://github.com/albertomh/django-sqlite-strict/commit/529ef1c6dcbf0bc9d3cdbf146df20469876a7015))
* Raise an exception when an incompatible sqlite detected ([#8](https://github.com/albertomh/django-sqlite-strict/issues/8)) ([9687d4e](https://github.com/albertomh/django-sqlite-strict/commit/9687d4e6ecc0b11da1267894518ed460847e628c))
* Raise error if any column incompatible with STRICT types ([#15](https://github.com/albertomh/django-sqlite-strict/issues/15)) ([b62be65](https://github.com/albertomh/django-sqlite-strict/commit/b62be65f2ceec135497aa4aac978a13812f54655))


### Documentation

* Add sections on prerequisites & installation to README ([#16](https://github.com/albertomh/django-sqlite-strict/issues/16)) ([b2f63ae](https://github.com/albertomh/django-sqlite-strict/commit/b2f63ae059388d0cd68f01e82f32e4005c26f9d1))
