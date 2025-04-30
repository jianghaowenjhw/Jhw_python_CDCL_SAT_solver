# SAT求解器 - 离散数学大作业

这个项目实现了一个基于CDCL（Conflict-Driven Clause Learning）算法的SAT求解器。该求解器能够解决布尔可满足性问题，并支持标准DIMACS CNF格式的输入。

## 文件结构

- `solver.py`：主要的SAT求解器实现，基于CDCL算法
- `to_test.py`：测试脚本，用于生成随机测试用例并与标准求解器比较结果
- `bf_SATsolver.exe`：暴力求解器，用作结果对比的标准
- `bf_satsolver.cpp`：暴力求解器的C++源代码

## 编译暴力求解器

暴力求解器使用C++编写，可以通过以下命令编译：

```bash
# 在项目根目录下执行
g++ bf_satsolver.cpp -o bf_SATsolver.exe
```

编译环境：
- 使用 MinGW-W64 g++ 8.1.0 (x86_64-posix-sjlj-rev0)
- 无需额外编译参数

如果需要在其他环境下编译，确保使用支持C++11或更高版本的编译器。

## 使用方法

### 直接使用求解器

求解器采用DIMACS CNF格式的标准输入，并将结果输出到标准输出。

#### 命令行使用示例：

```bash
# 从文件输入
python solver.py < input.cnf

# 使用调试模式
python solver.py --debug < input.cnf
```

#### Windows PowerShell特别说明：

在PowerShell中，您可以使用以下方式：

```powershell
# 从文件读取输入
Get-Content input.cnf | python solver.py

# 手动输入后结束（按Ctrl+Z然后Enter结束输入）
python solver.py
c 这是注释
p cnf 3 2
1 2 0
-2 3 0
[按Ctrl+Z然后Enter]
```

### 输入格式

DIMACS CNF格式示例：
```
c 这是注释行
p cnf 3 2
1 2 0
-2 3 0
```

- `c` 开头的行表示注释
- `p cnf 3 2` 表示有3个变量和2个子句
- 每个子句以0结尾，正数表示肯定文字，负数表示否定文字

### 输出格式

- `s SATISFIABLE` 或 `s UNSATISFIABLE` 表示求解结果
- 当结果是可满足时，会输出一个可能的解，例如：`v 1 -2 3 0`

### 使用测试脚本

测试脚本可以生成随机CNF公式，并比较我的求解器与标准求解器的结果。

```bash
python to_test.py
```

测试脚本会：
1. 生成随机SAT问题
2. 同时使用我的求解器和标准求解器求解
3. 比较两者的结果是否一致
4. 统计通过率
5. 将不一致的测试用例保存在`WRONG`目录中

## 算法说明

本求解器实现了CDCL算法，包含以下核心步骤：
1. 单元传播 (Unit Propagation)
2. 冲突检测 (Conflict Detection)
3. 冲突分析和子句学习 (Conflict Analysis and Clause Learning)
4. 回溯 (Backtracking)
5. 决策变量选择 (Decision Variable Selection)

## 注意事项

- 代码中包含了调试选项，在需要查看详细解决过程时非常有用
- to_test.py与这个README.md是AI生成的
