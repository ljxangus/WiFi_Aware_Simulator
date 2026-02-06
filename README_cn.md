# Wi-Fi Aware (NAN) 协议仿真器

基于 SimPy 的 Wi-Fi 邻居感知网络 (NAN) 高保真仿真器，支持 IEEE 802.11-2016 附录 AQ 和 WFA NAN 3.1/4.0 规范。

## 功能特性

- **协议合规性**: 实现 NAN 集群形成、发现窗口和服务发现
- **TSF 同步**: 时钟同步函数与时钟漂移建模
- **服务发现**: 发布/订阅状态机及匹配过滤
- **NDP 支持**: NAN 数据接口用于数据路径建立
- **移动性模型**: 静态和随机游走移动模型
- **能耗建模**: 详细的功耗跟踪 (休眠/监听/接收/发送状态)
- **信道建模**: 对数距离路径损耗与 CSMA/CA
- **统计分析**: 综合指标收集与 CSV/JSON 导出

## 项目结构

```
WiFi_Aware_Simulator/
├── config/                 # 配置文件
│   ├── default.yaml        # 默认仿真参数
│   └── scenarios/          # 场景预设
├── src/                    # 源代码
│   ├── core/              # 核心仿真引擎
│   ├── nan/               # NAN 协议 (集群、TSF、角色)
│   ├── discovery/         # 服务发现 (DW、发布/订阅)
│   ├── phy_mac/           # PHY/MAC 层 (信道、帧、功耗)
│   ├── ndp/               # 数据路径 (NDI、调度)
│   ├── node/              # 节点实现
│   └── utils/             # 统计和日志
├── examples/              # 示例脚本
├── tests/                 # 单元测试
└── output/                # 仿真结果
```

## 安装

### 环境要求

- Python 3.10+
- SimPy 4.0+
- PyYAML, NumPy, Pandas

### 安装步骤

#### 方法 1: 使用虚拟环境 (推荐)

```bash
# 克隆仓库
git clone https://github.com/ljxangus/WiFi_Aware_Simulator.git
cd WiFi_Aware_Simulator

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装包 (可选)
pip install -e .
```

#### 方法 2: 使用系统 Python

```bash
# 克隆仓库
git clone https://github.com/ljxangus/WiFi_Aware_Simulator.git
cd WiFi_Aware_Simulator

# 安装依赖
pip install -r requirements.txt

# 安装包 (可选)
pip install -e .
```

#### 验证安装

```bash
# 运行测试验证安装
pytest tests/ -v

# 运行基础示例
python examples/basic_discovery.py
```

## 快速开始

> **提示**: 如果使用虚拟环境，请先激活虚拟环境：
> ```bash
> source venv/bin/activate  # macOS/Linux
> venv\Scripts\activate     # Windows
> ```

### 基础服务发现示例

```python
from src.core.simulation import Simulation

# 使用默认配置创建仿真
sim = Simulation()

# 运行 30 秒
sim.run(duration=30000)

# 结果导出到 output/ 目录
```

### 使用自定义配置

```yaml
# config/my_scenario.yaml
node:
  count: 50              # 节点数量
  area_size: [200, 200]  # 仿真区域 (米)

time:
  dw_interval: 512       # 发现窗口间隔 (毫秒)
  dw_duration: 16        # 发现窗口持续时间 (毫秒)

simulation:
  duration: 60000        # 仿真时长 (毫秒)
  seed: 123             # 随机种子
```

```python
sim = Simulation(config_path='config/my_scenario.yaml')
sim.run()
```

### 命令行运行

```bash
# 如果使用虚拟环境，先激活虚拟环境：
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate     # Windows

# 使用默认配置运行
python -m src.core.simulation

# 使用自定义配置运行
python -m src.core.simulation config/scenarios/high_density.yaml

# 运行基础发现示例
python examples/basic_discovery.py

# 运行 NDP 数据路径示例
python examples/ndp_example.py
```

## 配置说明

### 主要参数

| 参数 | 说明 | 默认值 |
|-----------|-------------|---------|
| `node.count` | 节点数量 | 20 |
| `time.dw_interval` | 发现窗口间隔 (毫秒) | 512 |
| `time.dw_duration` | 发现窗口持续时间 (毫秒) | 16 |
| `mobility.enabled` | 启用移动性 | true |
| `mobility.model` | 移动模型 (random_walk/static) | random_walk |
| `simulation.duration` | 仿真时长 (毫秒) | 60000 |
| `simulation.seed` | 随机种子 | 42 |

### 功耗状态

- **Sleep (休眠)**: 1 mW (默认)
- **Listen (监听)**: 200 mW (默认)
- **RX (接收)**: 300 mW (默认)
- **TX (发送)**: 800 mW (默认)

## 输出文件

### CSV 文件

- `simulation_*_discovery_latency.csv` - 每次发现的延迟
- `simulation_*_power.csv` - 每个节点的能耗
- `simulation_*_service_discovery.csv` - 服务发现事件

### JSON 摘要

- `simulation_*_summary.json` - 汇总统计数据

### 关键指标

- **发现延迟**: 从订阅到发现的时间
- **能耗**: 总能耗和各状态能耗
- **跳数分布**: 到锚主站的距离
- **成功率**: 发现服务的百分比

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_cluster.py -v

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

## 架构设计

### NAN 集群

```
┌─────────────────────────────────────┐
│         NAN 集群                      │
│  ┌─────────────────────────────┐    │
│  │  锚主站 (AM)                │    │
│  │  - 最高优先级               │    │
│  │  - 发送信标                 │    │
│  └─────────────────────────────┘    │
│           ↑                           │
│  ┌────────┴────────┐                 │
│  │  NMS (1 跳)     │                 │
│  │  - 转发         │                 │
│  │    信标         │                 │
│  └─────────────────┘                 │
│           ↑                           │
│  ┌────────┴────────┐                 │
│  │  NMNS (2+ 跳)   │                 │
│  │  - 普通         │                 │
│  │    设备         │                 │
│  └─────────────────┘                 │
└─────────────────────────────────────┘
```

### 发现窗口时序

```
时间 ──────────────────────────────────────────────→

┌────────┐     ┌────────┐     ┌────────┐
│   DW   │     │   DW   │     │   DW   │
│  16ms  │     │  16ms  │     │  16ms  │
└────────┘     └────────┘     └────────┘
   512ms         512ms         512ms

社交信道 6           社交信道 149
(信标 + SDF)         (信标 + SDF)
```

## 性能

### 可扩展性

- **小规模**: 10 个节点，30 秒仿真时间 ≈ 5 秒运行时间
- **中等规模**: 50 个节点，60 秒仿真时间 ≈ 30 秒运行时间
- **大规模**: 100+ 个节点 (需要优化)

### 内存占用

- 基础: ~50 MB
- 每个节点: ~2 MB
- 50 个节点: ~150 MB

## 标准合规性

- **IEEE 802.11-2016 附录 AQ**: NAN 协议基础
- **WFA NAN 规范 3.1**: 服务发现
- **WFA NAN 规范 4.0**: NDP 数据路径

## 局限性

- 简化的碰撞检测 (无捕获效应)
- 基础路由 (跳数估算)
- 无安全/加密
- 每个 DW 仅单个社交信道

## 未来工作

- [ ] 多集群同步
- [ ] 高级移动性模型 (RWP、高斯-马尔可夫)
- [ ] NDP 数据传输仿真
- [ ] 实时可视化
- [ ] 网络层集成

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 为新功能添加测试
4. 确保所有测试通过
5. 提交 Pull Request

## 许可证

MIT License - 详见 LICENSE 文件

## 参考文献

- IEEE 802.11-2016 标准，附录 AQ
- Wi-Fi Alliance NAN 规范 v3.1
- Wi-Fi Alliance NAN 规范 v4.0

## 引用

如果您在研究中使用此仿真器，请引用：

```bibtex
@software{wifi_aware_simulator,
  title={Wi-Fi Aware (NAN) Protocol Simulator},
  author={Jiaxin Liang},
  year={2026},
  url={https://github.com/ljxangus/WiFi_Aware_Simulator}
}
```

## 联系方式

如有问题、建议或贡献意向，请提交 GitHub Issue。
