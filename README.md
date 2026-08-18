# 运行：`pytest test_cases/test_booking.py --html=reports/report.html --self-contained-html -v`

# 冒烟测试运行：`pytest -m smoke --html=reports/smoke_report.html --self-contained-html`

# API接口自动化测试项目 —— 基于 Restful-Booker

一个基于在线测试系统 [Restful-Booker](https://restful-booker.herokuapp.com) 的接口自动化测试项目，技术栈为 **Python + requests + pytest**，覆盖鉴权、增删改查、边界场景，并接入 GitHub Actions 实现自动化 CI。

---

## 目录

- [项目背景](#项目背景)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [运行测试](#运行测试)
- [测试用例说明](#测试用例说明)
- [CI/CD 自动化](#cicd-自动化)
- [踩坑记录](#踩坑记录)
- [后续计划](#后续计划)

---

## 项目背景

选择 [Restful-Booker](https://restful-booker.herokuapp.com) 作为测试目标，而非常见的 mock 接口（如 reqres.in），是因为它专门为接口测试练习设计，具备真实系统的关键特征：

- 有完整的**登录鉴权机制**（先登录拿 token，再用 token 做增删改）
- 模拟真实业务场景（酒店预订系统），字段带业务含义
- 故意植入了一些边界行为，适合练习"发现问题"而非只验证"功能正常"

项目目标：从0到1搭建一套可扩展的接口自动化测试框架，覆盖正向用例、边界用例、鉴权用例，并实现 CI 自动化。

---

## 技术栈

| 类别     | 工具                   |
| -------- | ---------------------- |
| 语言     | Python 3.11            |
| HTTP请求 | requests               |
| 测试框架 | pytest                 |
| 报告生成 | pytest-html            |
| 依赖管理 | pip + requirements.txt |
| CI/CD    | GitHub Actions         |

---

## 项目结构

```
api-test-booker/
├── config/
│   └── settings.py          # 全局配置：BASE_URL、测试账号密码
├── test_cases/
│   └── test_booking.py      # 测试用例：登录、CRUD、边界、鉴权
├── conftest.py               # 全局fixture：登录token、创建测试数据
├── reports/                   # pytest-html 生成的测试报告（不提交到git）
├── .github/
│   └── workflows/
│       └── test.yml          # GitHub Actions CI配置
├── requirements.txt           # 项目依赖清单
├── .gitignore
└── README.md
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/wangxiuchun/api-test-booker.git
cd api-test-booker
```

### 2. 创建并激活虚拟环境

```bash
python -m venv venv
```

激活虚拟环境：

| 系统        | 命令                       |
| ----------- | -------------------------- |
| Windows     | `venv\Scripts\activate`    |
| Mac / Linux | `source venv/bin/activate` |

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

---

## 运行测试

### 运行全部测试用例，并生成HTML报告

```bash
pytest test_cases/ --html=reports/report.html --self-contained-html -v
```

- `-v`：终端打印每条用例的详细执行情况
- `--html=reports/report.html`：指定报告输出路径
- `--self-contained-html`：把CSS/JS打包进单个文件，方便直接分享查看

运行完成后，打开 `reports/report.html` 即可查看带通过率、用例详情的可视化报告。

### 只运行单个测试文件

```bash
pytest test_cases/test_booking.py -v
```

### 只运行某一个测试函数

```bash
pytest test_cases/test_booking.py::test_auth_returns_token -v
```

---

## 测试用例说明

| 用例                                       | 覆盖场景                                 |
| ------------------------------------------ | ---------------------------------------- |
| `test_auth_returns_token`                  | 验证登录接口能正常返回token              |
| `test_create_booking`                      | 验证创建预订后，数据能被正确查询到       |
| `test_get_nonexistent_booking_returns_404` | 边界测试：查询不存在的资源应返回404      |
| `test_update_without_token_should_fail`    | 鉴权测试：不带token更新，应被拒绝（403） |
| `test_delete_without_token_should_fail`    | 鉴权测试：不带token删除，应被拒绝（403） |
| `test_create_booking_with_various_prices`  | 参数化测试：多组价格数据批量验证         |

设计原则：

- **fixture隔离**：`auth_token` 使用 `scope="session"`，整个测试运行期间只登录一次；`created_booking` 默认 `function` 级别，每个用例独立创建数据，避免互相干扰
- **正向+反向都覆盖**：不仅测"正常能不能用"，也测"异常场景是否被正确拦截"（未授权访问、查询不存在的资源）

---

## CI/CD 自动化

项目接入 GitHub Actions，每次 push 到 `main` 分支或发起 Pull Request 时，会自动：

1. 拉取代码
2. 搭建 Python 3.11 环境
3. 安装依赖
4. 运行全部测试用例
5. 上传测试报告作为 Artifact（即使测试失败也会上传，方便排查）

查看运行结果：仓库页面 → **Actions** 标签页 → 点击对应的运行记录 → 下方 **Artifacts** 区域下载报告。

配置文件见 [`.github/workflows/test.yml`](.github/workflows/test.yml)。

---

## 踩坑记录

### 1. 登录失败时接口返回200，而不是401/400

`/auth` 接口在账号密码错误时，依然返回状态码200，只是响应体里是 `{"reason": "Bad credentials"}`，没有 `token` 字段。如果代码直接用 `response.json()["token"]` 取值，会在密码错误时抛出 `KeyError`，而不是被 `assert status_code == 200` 这行拦截。

**排查方式**：在fixture里临时打印完整响应内容，加 `-s` 参数让pytest显示print输出：

```bash
pytest test_cases/test_booking.py::test_auth_returns_token -v -s
```

### 2. 未授权操作返回403，而非常见的401

不带token调用更新/删除接口时，Restful-Booker返回的是 **403 Forbidden**，不是更常见的 **401 Unauthorized**。写断言时不能想当然假设状态码，需要先实测确认接口真实行为，再写死断言，而不是用 `in (401, 403)` 这种模糊判断掩盖过去。

### 3. .gitignore要在第一次commit之前配置好

如果 `.gitignore` 是在 `venv/` 已经被提交之后才补充内容，Git依然会继续追踪已提交的文件，需要额外执行：

```bash
git rm -r --cached venv/
git rm -r --cached reports/
```

`--cached` 参数的作用是只从Git追踪记录里移除，不删除本地真实文件。

### 4. 国内访问GitHub偶发超时

`git pull`/`git push` 时可能遇到 `Failed to connect to github.com port 443: Timed out`，通常是网络问题，非命令本身错误。排查顺序：确认VPN是否开启 → 检查Git是否需要手动配置代理：

```bash
git config --global http.proxy http://127.0.0.1:端口号
git config --global https.proxy http://127.0.0.1:端口号
```

---

## 后续计划

- [ ] 补充更多参数化边界case（必填字段缺失、错误数据类型）
- [ ] 用 `@pytest.mark` 划分冒烟测试/回归测试，支持按标记选择性运行
- [ ] 增加请求日志记录，方便失败时排查具体请求/响应内容
- [ ] 尝试性能维度：批量并发创建预订，观察响应时间变化
