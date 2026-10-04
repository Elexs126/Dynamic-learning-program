# 离线公式渲染

- MathJax 3.2.2，`es5/tex-svg.js`，来自固定版本包：<https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js>。
- 上游项目：<https://github.com/mathjax/MathJax>。
- `tex-svg.js` SHA-256：`d4295dc33744836935c1399feece5159577b34c5c8ffb9f1c6324cd82e03a882`。
- Apache 2.0许可证原文保存于 `MATHJAX-LICENSE.txt`，来自同版本包的LICENSE。

组卷时校验上述哈希并内嵌脚本；SVG公式字体随组件提供，正常公式无需网络资源。更新版本时同步库、许可证与脚本中的哈希常量，并复测公式页面。不自动从CDN获取最新版本。
