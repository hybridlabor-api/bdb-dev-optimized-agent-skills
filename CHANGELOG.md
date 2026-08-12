# Changelog

## [1.2.0](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/compare/v1.1.0...v1.2.0) (2026-08-12)


### Features

* add memB LLM proxy and Auto-Capture system (Phase A & C) ([2d29a0b](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/2d29a0b75c0e1b320e39e9e86a337172722cfe93))
* auto-copy Godmode/Harness directories to local workspace ([05181e2](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/05181e21ecdf67b4ab31b1149121963ab9874fe3))
* **harness:** scaffold universal agent harness directories for v3.0.0 ([b03e3c4](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/b03e3c4b2a9fc661dca2234345e293cb8795280e))
* **heimdall:** implement universal harness auto-injection for all major IDEs and CLIs ([1046ddd](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/1046dddb45075b80448fd2fdb2377b9ed2ebd315))
* **installer:** add automatic git clone fallback for creator extension and os agent workspace ([59f4f03](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/59f4f037cda4a41a3a1f5ee556d77329b148ed5c))
* **installer:** add interactive LLM provider selection for OpenWiki (Gemma/OpenAI/Ollama) ([20b85f6](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/20b85f6a3239763407ea50e4f1b82bb53f88e0ca))
* **installer:** add modular prompt to configure BDB Creator Extension ([43cd9d1](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/43cd9d1eb911cff7133b26ed3c2d0f39065ce79b))
* **installer:** automatically inject GEMINI.md global rules to all IDE harnesses ([aae6fc2](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/aae6fc29e796f43ff74a3c0b68ba95f26216d569))
* **installer:** implement interactive arrow key navigation for all menu prompts ([95a11b6](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/95a11b64b4783af4adc4fd9262bc6e4c1ac88036))
* **installer:** implement interactive arrow key navigation for all single-select prompts ([d00b0a2](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/d00b0a2b12a9e62097f0eb421bd6be1db222e158))
* **installer:** overhaul promptMode for Universal Agent Harness sync across all platforms ([14b9d71](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/14b9d7107fcd88e579f507cc66840c220c151a60))
* **installer:** pre-select already installed MCPs in the menu ([545192d](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/545192d7358991b34a66060da8634fe91e69affa))
* **installer:** switch ecosystem download from git clone to public npm package ([381ec85](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/381ec8589b71038dd42bd380f3ffd20f49810cd3))
* **mcp:** add open-design mcp server integration to installer ([b6305ff](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/b6305ffc5890670a4c504f536adcecd77e650bf3))
* **memb:** add memB auto-injection daemon for cursor, claude, and copilot ([ac26211](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/ac2621136f8c8ee290dd99ff7e7a795fe6c45231))
* **openwiki:** add 60s auto-refresh to code health dashboard HTML ([c70efda](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/c70efda52ea957c292031d62a8de54cc5a1a9189))
* **openwiki:** add deterministic code health report (hotspots, bus factor, commit freq) ([a56c78f](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/a56c78f3eef885f4d33860ad96cf305d4d7a6e82))
* **openwiki:** add support for Grok, Groq, Nvidia NIM, OpenRouter, Claude, Kimi, Qwen & custom OpenAI endpoints ([d64162a](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/d64162a95925c41cd37c63eff3cc6c5966473731))
* **openwiki:** full Repowise-grade RepoGraph dashboard with SVG scatter, dependency network & memB decisions ([f3a1067](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/f3a106759521dfb6d4c2dce39bf7c698c67033a7))
* **openwiki:** generate HTML dashboard for Code Health ([80b79ff](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/80b79ff12b9323763e953d46d792fae89720a1bf))
* replace manual mcp selection with interactive up/down arrow menu\nfix: execSync reference error in creator extension setup ([0b99f25](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/0b99f2571e81efb22e0fc97ed223a78c8452b838))
* **skills:** add 3 godmode meta-skills (ui-ux, engineering, shipping) ([2782cb9](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/2782cb9ee54a4dbb7025d0b8408248a5eeb32bbe))
* **skills:** add bdreadme formatting skill ([14bc3de](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/14bc3de665876e7bac98683afa8d763588ae99a2))
* **skills:** add creator-godmode to govern Creator Extension MCPs and fix markdown table layout ([ae0ab0f](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/ae0ab0fd23b21543bff64184fecfd2b9bff27edf))
* **skills:** enforce Creator Extension and MediaStorm governance within all Godmode skills ([8e291de](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/8e291dea73aa42c6aa0f618aae2ebfe22d0be719))
* **skills:** integrate 3 core godmodes into brainstorm and mediastorm workflows ([181bd9b](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/181bd9bb7669d57e854de6dfa797a52c9934ec5b))
* **skills:** merge bdreadme rules into github-repo skill and remove bdreadme ([3ab0ce7](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/3ab0ce77a9481a9d2f39d618e949c8126bb78317))


### Bug Fixes

* Allow installing single-file MCP servers like Resolume and grandMA3 ([a51fc67](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/a51fc67d33b02c2541850ee56873223db1349bdd))
* Codex CLI compatibility for memB MCP ([9038248](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/9038248177661a4466a37ac32f5dd55478b64a5f))
* **docs:** repair broken details tags in github markdown ([0bad32b](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/0bad32b86c85954ec7905293f6ef5833f792561a))
* **installer:** deploy bdb extensions to neutral .agents folder instead of .gemini ([4dc321a](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/4dc321a1af2bec2961600742cc2bfea2fded15b3))
* **installer:** unfreeze interactive mcp menu by resuming stdin ([047ea44](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/047ea444dc4daf0ff722348e454f19bbc619c160))
* **installer:** unify UI interactions across all menus, implement isolated keypress events to prevent TTY crashes ([b7a864a](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/b7a864a8bc124b1198d1806399414e38f0eb7632))
* **skills:** remove hardcoded BDB DEV strings from github-repo layout rules to make them universal ([40d51a2](https://github.com/hybridlabor-api/bdb-dev-optimized-agent-skills/commit/40d51a2e4f486214b3411cc1c836a17040b3487a))
