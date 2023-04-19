---
name: Bug report
about: Create a bug report to help us improve the blobconverter
title: "[BUG] "
labels: bug
assignees: ''

---

**Note**: Blobconverter is a simple wrapper around the OpenVINO tools, specifically:
- Model optimizer: https://docs.luxonis.com/en/latest/pages/model_conversion/#model-optimizer
- Compile tool: https://docs.openvino.ai/2021.4/openvino_inference_engine_tools_compile_tool_README.html

Most of the time, if the blobconverter returns an error, it's an **error thrown by Model Optimizer / Compile tool, NOT by blobconverter itself**. So please
don't report such issues here, but on OpenVINO github: https://github.com/openvinotoolkit/openvino

For converting model to blob, see documentation here: https://docs.luxonis.com/en/latest/pages/model_conversion/

**Describe the bug**
A clear and concise description of what the bug is.
