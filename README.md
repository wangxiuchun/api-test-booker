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
├── utils/
│   ├── __init__.py
│   └── http_client.py        # 统一HTTP客户端：拼接URL、自动记录请求/响应日志
├── test_cases/
│   └── test_booking.py      # 测试用例：登录、CRUD、边界、鉴权、已知缺陷
├── conftest.py               # 全局fixture：登录token、创建测试数据
├── pytest.ini                 # 注册smoke/regression标记
├── reports/                   # 测试报告+运行日志（不提交到git）
│   ├── report.html            # pytest-html 生成的可视化报告
│   └── api_test.log           # 完整请求/响应日志
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

### 按标记（marker）选择性运行

项目用 `pytest.ini` 注册了两类标记，方便按需选择性运行：

- `smoke`：冒烟测试，核心链路（登录、创建），验证系统基本能用
- `regression`：完整回归测试，覆盖边界、鉴权、已知缺陷

```bash
# 只跑冒烟测试（核心链路，快速验证）
pytest -m smoke -v

# 只跑回归测试（边界+鉴权+已知缺陷）
pytest -m regression -v

# 查看当前项目注册了哪些标记
pytest test_cases/test_booking.py --markers
```

---

## 测试用例说明

| 用例                                                       | 标记         | 覆盖场景                                                                                    |
| ---------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------- |
| `test_auth_returns_token`                                  | `smoke`      | 验证登录接口能正常返回token                                                                 |
| `test_create_booking`                                      | `smoke`      | 验证创建预订后，数据能被正确查询到                                                          |
| `test_get_nonexistent_booking_returns_404`                 | `regression` | 边界测试：查询不存在的资源应返回404                                                         |
| `test_update_without_token_should_fail`                    | `regression` | 鉴权测试：不带token更新，应被拒绝（403）                                                    |
| `test_delete_without_token_should_fail`                    | `regression` | 鉴权测试：不带token删除，应被拒绝（403）                                                    |
| `test_create_booking_with_invalid_data`（参数化，3组数据） | `regression` | 已知缺陷记录：缺失字段导致500、非法类型/日期被静默写入脏数据（详见[踩坑记录](#踩坑记录)）   |
| `test_concurrent_booking_creation`（参数化，5/10/15并发）  | `regression` | 性能维度：不同并发梯度下的响应时间与成功率，观察响应时间波动性（详见[踩坑记录](#踩坑记录)） |

设计原则：

- **fixture隔离**：`auth_token` 使用 `scope="session"`，整个测试运行期间只登录一次；`created_booking` 默认 `function` 级别，每个用例独立创建数据，避免互相干扰
- **正向+反向都覆盖**：不仅测"正常能不能用"，也测"异常场景是否被正确拦截"（未授权访问、查询不存在的资源、非法输入）
- **分层标记**：`smoke` 覆盖核心链路，用于快速验证；`regression` 覆盖边界、鉴权、已知缺陷，用于完整回归
- **统一请求出口**：所有用例通过 `utils/http_client.py` 发起请求，而非直接调用 `requests`，请求URL自动拼接、请求响应自动记录进 `reports/api_test.log`

---

## CI/CD 自动化

项目接入 GitHub Actions，每次 push 到 `main` 分支或发起 Pull Request 时，自动触发**分层执行**的测试流程：

1. **冒烟测试（smoke-test）**：先跑核心链路（登录、创建），快速验证系统基本能用
2. **完整回归测试（regression-test）**：通过 `needs: smoke-test` 依赖冒烟测试的结果——只有冒烟测试通过，才会启动，跑边界、鉴权、已知缺陷等完整场景

两个job分别生成独立的HTML报告，作为Artifact单独上传，互不覆盖。

**分层的意义**：如果核心链路已经出问题，没必要浪费时间和CI资源去跑完整回归；只有确认地基没塌，才值得花更多时间检查细节。这个模式随着用例数量增长（几十上百条）价值会更明显——用最短时间给出"系统能不能用"的信号，完整覆盖可以放在后面。

查看运行结果：仓库页面 → **Actions** 标签页 → 点击对应的运行记录，能看到两个job的执行顺序和各自耗时；下方 **Artifacts** 区域可分别下载 `smoke-report` 和 `regression-report`。

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

### 5. `__pycache__` / `.pytest_cache` 被误提交

`.gitignore` 里加了忽略规则，但如果这些目录在补充规则**之前**就已经被 `git add` 提交过，规则不会自动生效——Git会继续追踪已经进入历史记录的文件。需要额外执行：

```bash
git rm -r --cached __pycache__/
git rm -r --cached .pytest_cache/
```

排查是否已被误提交，可以用（Windows PowerShell下 `grep` 需替换成 `Select-String`）：

```powershell
git ls-files | Select-String pycache
```

### 6. 发现的三个真实接口缺陷

在边界测试阶段，针对 `/booking` 创建接口测试了三种不合法输入，发现该接口**完全没有做输入校验**：

| 场景                                     | 期望行为             | 实际行为                                               |
| ---------------------------------------- | -------------------- | ------------------------------------------------------ |
| 缺少必填字段 `firstname`                 | 返回 400 Bad Request | 返回 **500 Internal Server Error**（服务端未捕获异常） |
| `totalprice` 传入非数字类型（字符串）    | 拒绝请求或返回400    | 返回200成功，但字段被**静默置为 `null`**               |
| `checkin` 传入不存在的日期（如13月99日） | 拒绝请求或返回400    | 返回200成功，但日期被写入脏数据 `"0NaN-aN-aN"`         |

这三个发现被固化成测试用例（`test_create_booking_with_invalid_data`），断言的是"当前的真实缺陷行为"而非"理想中应该发生的行为"——这样一旦这些问题被修复，对应用例会转为失败，从而提示"已知缺陷的状态发生了变化，需要重新确认"，这正是回归测试用来追踪缺陷生命周期的作用。

### 7. 本地环境和CI环境的目录状态不是天然一致的

给项目加了统一HTTP客户端（`utils/http_client.py`）后，其中用 `logging.FileHandler` 把请求日志写入 `reports/api_test.log`。本地一直能正常运行，是因为之前手动执行过 `mkdir -p reports`，本地磁盘上这个目录一直存在。

但接入CI分层后，第一次运行直接失败，报错是 `exit code 4`，报告文件也没生成。原因是：**`reports/` 目录被 `.gitignore` 排除，从未提交到仓库**，而GitHub Actions每次都在全新的虚拟机上运行，拉取代码后根本没有这个文件夹。`logging.FileHandler` 不会自动创建目录，模块被导入的那一刻（`conftest.py` 执行 `import`）就直接崩溃，连测试用例都还没开始跑。

**解决方式（两边都加，双保险）**：

1. CI配置里，运行测试前加一步显式创建目录：
   ```yaml
   - name: 创建reports目录
     run: mkdir -p reports
   ```
2. 代码里让程序自己保证目录存在，不依赖外部环境提前建好：
   ```python
   import os
   os.makedirs("reports", exist_ok=True)  # 加在logging.basicConfig之前
   ```

这个坑的通用教训：**不能假设本地手动建过的文件夹，在任何运行环境里都天然存在**——凡是代码依赖某个目录/文件先存在，要么在代码里做防御性创建，要么在部署/CI流程里显式声明，两者选一，最好两者都做。

### 8. 并发测试时VPN环境导致连接被中止，靠"连接池复用+自动重试"解决

给项目加了一个性能维度的用例（`test_concurrent_booking_creation`），用 `ThreadPoolExecutor` 同时发起多个创建预订请求，观察响应时间和成功率。排查过程中遇到的问题和解决路径，完整记录如下：

```
20并发 + VPN开启 → ConnectionAbortedError(10053)：本地软件中止了已建立的连接
        ↓
关闭VPN重试 → ConnectTimeout：连不上Heroku服务器
        （证实访问 restful-booker.herokuapp.com 必须保持VPN开启）
        ↓
降到5并发 + VPN开启 → 仍然是10053
        （说明不是并发数量的问题，而是VPN处理并发连接本身不稳定）
        ↓
给 http_client.py 引入 requests.Session + HTTPAdapter 连接池复用
        → 单组5并发能稳定通过
        → 但5/10/15三组连续跑（累计30次请求）又开始失败
        （说明短时间内的请求总量/频率也会触发同样的问题）
        ↓
在 HTTPAdapter 上叠加 urllib3.Retry 自动重试策略
        （最多重试3次，重试间隔按0.5秒递增，一并覆盖5xx服务端错误）
        → 5/10/15三组梯度全部稳定通过
```

**关键结论**：

- 这个问题本质是**本地网络环境（VPN客户端）在处理并发/连续请求时不稳定**，不是被测系统或测试代码的问题
- **`requests.Session` + 连接池**解决的是"重复建立TCP连接"带来的开销和压力，**`Retry` 自动重试**解决的是"偶发的瞬时连接中断"——两者作用层面不同，需要一起用才能覆盖完整的网络抖动场景，这也是真实项目里应对网络不稳定的标准组合
- 15并发下观察到的数据：平均耗时0.67秒，但最长1.57秒、最短仅0.23秒，波动幅度接近7倍——**响应时间的波动性会随并发量上升而明显放大**，这比单看平均值更能反映系统在压力下的真实表现

**最终配置**（`utils/http_client.py`）：

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_session = requests.Session()
_retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
)
_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=_retry_strategy)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)
```

---

## 后续计划

- [x] 补充更多参数化边界case（必填字段缺失、错误数据类型），并发现3个真实接口缺陷
- [x] 用 `@pytest.mark` 划分冒烟测试/回归测试，支持按标记选择性运行
- [x] 增加请求日志记录，封装统一HTTP客户端，方便失败时排查具体请求/响应内容
- [x] CI分层：`smoke` 冒烟测试通过后才触发 `regression` 完整回归测试
- [x] 尝试性能维度：批量并发创建预订，观察响应时间变化，并解决了本地VPN环境下的并发连接不稳定问题
