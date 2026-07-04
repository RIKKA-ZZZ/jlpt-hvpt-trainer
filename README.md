# JLPT HVPT Trainer

一个非官方的 JLPT 词汇训练小网站，当前包含：

- 看词选图练习
- 听音选词练习
- N5 / N4 词汇数据
- 本地 AI 生成图片素材

## 本地运行

打开：

```text
hvpt_site/start_site.bat
```

然后访问本地页面。现在首页是开屏介绍页，点击“开始训练”会进入 `hvpt_site/trainer.html`。
这个项目目前主要按本地静态网站设计。

## 分享给别人

可以把整个项目文件夹压缩给别人。对方解压后进入 `hvpt_site`，双击 `start_site.bat` 即可打开网站。

注意：

- 不建议直接双击 `index.html`，因为浏览器可能会拦截本地 JSON 数据读取。
- 对方电脑需要安装 Python。脚本会自动尝试 `py -3` 或 `python`。
- 对方不需要安装 ComfyUI，也不需要有生成模型；网站运行只需要已经生成好的 `hvpt_site/data` 和 `hvpt_site/assets/images`。
- 如果只是给别人体验网站，建议只打包 `hvpt_site`、`README.md`、`NOTICE.md`、`LICENSE`，不要打包原始生成目录和临时文件。

## 来源与许可

公开发布前请阅读：

- `NOTICE.md`
- `hvpt_site/sources.html`

简要说明：

- 原创代码按 `LICENSE` 中的代码许可处理。
- Tanos JLPT 词表需要署名。
- JMdict/EDICT 派生释义按 CC BY-SA 4.0 或兼容许可处理。
- 图片是用户本地使用 ComfyUI + Animagine XL 4.0 生成，需要保留模型来源和许可说明。
- 本项目不是 JLPT 官方项目，也不包含官方真题或官方标志。

## 发布建议

如果发布到 GitHub，建议保留 `NOTICE.md`、`LICENSE`、`hvpt_site/sources.html`，并确认没有上传临时文件、原始抓取内容、第三方音频或未经确认许可的素材。
