# 贡献约定

先读AGENTS与当前backlog。文档和commit使用简体中文，commit一句简短描述真实改进。保留上游作者和许可证，新增驱动补丁按相应内核贡献要求提供Signed-off-by；不要替他人伪造署名。

每次逻辑改进：说明问题和现有证据→修改→适度相关验证→更新状态/限制/回退→运行公开检查→提交。需要CI通过、实机通过的范围分别标明。无硬件时欢迎提交分析或构建结果，但不要声称硬件已修复。

```bash
python3 scripts/qa/check.py
python3 -m unittest discover -s tests -v
git diff --check
git diff --cached
# 例：git commit -m '修复默认充电电流查询'
```

不向Git或Release提交凭据和私钥，禁止把大二进制放进源码历史。发布流程见docs/ARCHIVING.md。普通变更完成后提交；不要强推或覆盖其他人的改动。第一次导入的提交是今天对历史成果的整理，而不是追造历史开发记录。
