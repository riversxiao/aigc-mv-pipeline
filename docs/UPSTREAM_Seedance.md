# Seedance 制作方法的 H3 适配记录

参考项目：[Emily2040/seedance-2.0](https://github.com/Emily2040/seedance-2.0)，
参考版本 `4668457e560eee06e95d7fcfdf441c8c0bba802e`，吸收日期 2026-11-06。

采用其镜头表、参考职责分配、带证据的逐条验收和定向重拍思路。
本地实现为 `directing.py`、`motion_assets.py`、`shot_review.py`，接入本项目的 H3 提示词和任务身份。
没有安装上游完整 Skill、执行安装器或调用其 Seedance 服务。上游 Seedance 的标签、时长、
提示词长度或平台接口规则不当作 H3 规则使用。骨骼输入仍是 H3 原生视频视觉参考。

参考文件：

- [Shot Table](https://github.com/Emily2040/seedance-2.0/blob/4668457e560eee06e95d7fcfdf441c8c0bba802e/references/shot-table.md)
- [Reference Transfer Contract](https://github.com/Emily2040/seedance-2.0/blob/4668457e560eee06e95d7fcfdf441c8c0bba802e/references/reference-transfer-contract.md)
- [Retake Protocol](https://github.com/Emily2040/seedance-2.0/blob/4668457e560eee06e95d7fcfdf441c8c0bba802e/references/retake-protocol.md)

本项目检查字段完整性、来源和任务对应关系；它不自动评价表演是否优美、不自动证明口型正确。
上游文档中的概念例子或测试通过也不作为本项目成片质量的证明。

上游许可声明（MIT）：

```text
MIT License

Copyright (c) 2026 Iamemily2050 (@iamemily2050)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
