# Model Hosting Container Standards

Python toolkit for standardized model hosting container implementations with Amazon SageMaker integration.

## Overview

This repository provides a Python toolkit that enables TensorRT-LLM and vLLM integration with Amazon SageMaker hosting platform for efficient model deployment and inference.

## Repository Structure

```
ModelHostingContainerStandards/
├── python/                    # Python implementation
│   ├── model_hosting_container_standards/  # Python package
│   ├── examples/              # Python examples
│   ├── tests/                 # Python tests
│   ├── pyproject.toml         # Python project configuration
│   ├── Makefile               # Build automation
│   └── README.md              # Python-specific documentation
├── Config                     # Shared configuration files
└── README.md                  # This file
```

## Quick Start

```bash
cd python
poetry install
poetry shell
```

See the [Python README](./python/README.md) for detailed usage instructions, examples, and development workflow.

## Contributing

When contributing to this repository:

1. Place Python-specific code in the `python/` directory
2. Follow the established patterns for project structure
3. Include tests for new functionality
4. Update documentation as needed
5. Run pre-commit hooks to ensure code quality

## License

TBD
