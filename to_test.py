import random
import subprocess
import os
import time
from pathlib import Path

def generate_random_cnf(num_vars, num_clauses):
    """
    生成随机CNF公式的DIMACS格式字符串，大幅优化以提高SAT概率
    
    子句长度概率分布:
    - 长度为1的概率: 0.005 (降低单子句概率)
    - 长度为2的概率: 0.25
    - 长度为3的概率: 0.745
    
    优化策略:
    1. 平衡正负变量出现频率
    2. 避免变量在多个单子句中出现矛盾
    3. 确保子句组合不会导致明显的不可满足
    4. 模拟部分变量赋值，确保至少有一条满足路径
    5. 控制子句密度，避免过度约束
    
    Args:
        num_vars: 变量数量
        num_clauses: 子句数量
    
    Returns:
        DIMACS格式的CNF公式字符串
    """
    # 如果子句数过多，可能导致过约束，进行动态调整
    clause_var_ratio = num_clauses / max(1, num_vars)
    if clause_var_ratio > 4.2:  # 经验阈值：SAT问题通常在此比率以下更容易满足
        effective_clauses = min(num_clauses, int(num_vars * 4.2))
    else:
        effective_clauses = num_clauses
    
    lines = [f"p cnf {num_vars} {effective_clauses}"]
    
    # 记录每个变量正负出现的次数
    var_occurrence = {i: {'pos': 0, 'neg': 0} for i in range(1, num_vars + 1)}
    
    # 记录单子句约束
    unit_clauses = {}  # 存储变量的指定值，如 {1: True} 表示变量1为True
    
    # 模拟部分变量赋值，确保有一条满足路径
    # 随机为约20%的变量预先分配值
    assigned_vars = {}
    if num_vars >= 5:
        assigned_count = max(1, int(num_vars * 0.2))
        for _ in range(assigned_count):
            var = random.randint(1, num_vars)
            if var not in assigned_vars:
                assigned_vars[var] = random.choice([True, False])
    
    for _ in range(effective_clauses):
        # 修改子句长度概率
        rand = random.random()
        if rand < 0.005:  # 降低单子句概率
            clause_length = 1
        elif rand < 0.255:  # 0.005 + 0.25
            clause_length = 2
        else:
            clause_length = 3
        
        # 确保子句长度不超过可用变量数
        clause_length = min(clause_length, num_vars)
        
        if clause_length == 1:
            # 对单子句特殊处理，避免直接矛盾
            available_vars = []
            for var in range(1, num_vars + 1):
                # 如果变量没有在单子句中出现过，则可用
                if var not in unit_clauses:
                    available_vars.append(var)
            
            if not available_vars:
                # 如果没有可用变量，尝试改为长度2的子句
                clause_length = 2
                if num_vars < 2:
                    # 如果变量数不足，只能用单子句
                    var = random.randint(1, num_vars)
                    # 选择一致的值
                    if var in assigned_vars:
                        is_positive = assigned_vars[var]
                    else:
                        is_positive = random.random() > 0.5
                    
                    literal = var if is_positive else -var
                    clause = [literal]
                    unit_clauses[var] = is_positive
                    
                    # 更新变量出现次数
                    if is_positive:
                        var_occurrence[var]['pos'] += 1
                    else:
                        var_occurrence[var]['neg'] += 1
                    
                    clause_str = " ".join(map(str, clause)) + " 0"
                    lines.append(clause_str)
                    continue
            else:
                # 随机选择一个可用变量
                var = random.choice(available_vars)
                
                # 根据预分配值或出现次数决定正负
                if var in assigned_vars:
                    is_positive = assigned_vars[var]
                else:
                    pos_count = var_occurrence[var]['pos']
                    neg_count = var_occurrence[var]['neg']
                    
                    if pos_count > neg_count:
                        # 如果正出现更多，倾向于生成负变量
                        is_positive = random.random() > 0.7
                    elif neg_count > pos_count:
                        # 如果负出现更多，倾向于生成正变量
                        is_positive = random.random() < 0.7
                    else:
                        # 平均情况，随机决定
                        is_positive = random.random() > 0.5
                
                literal = var if is_positive else -var
                clause = [literal]
                unit_clauses[var] = is_positive
                
                # 更新变量出现次数
                if is_positive:
                    var_occurrence[var]['pos'] += 1
                else:
                    var_occurrence[var]['neg'] += 1
                
                clause_str = " ".join(map(str, clause)) + " 0"
                lines.append(clause_str)
                continue
        
        # 处理长度为2或3的子句
        # 尝试包含至少一个预分配为True的变量，确保子句可满足
        ensure_sat = (random.random() < 0.7)  # 70%概率确保子句可满足
        
        if ensure_sat and assigned_vars:
            # 选择一个预分配变量加入子句
            sat_var, sat_value = random.choice(list(assigned_vars.items()))
            
            # 使子句包含这个满足变量
            sat_literal = sat_var if sat_value else -sat_var
            
            # 剩余变量随机选择
            remaining_vars = list(set(range(1, num_vars + 1)) - {sat_var})
            if len(remaining_vars) >= clause_length - 1:
                remaining_selected = random.sample(remaining_vars, clause_length - 1)
                clause_vars = [sat_var] + remaining_selected
                
                # 创建子句
                clause = [sat_literal]  # 确保这个变量使子句满足
                
                # 为剩余变量决定正负性
                for var in remaining_selected:
                    pos_count = var_occurrence[var]['pos']
                    neg_count = var_occurrence[var]['neg']
                    
                    # 基于出现频率平衡正负
                    if pos_count > neg_count:
                        is_positive = random.random() > 0.6
                    elif neg_count > pos_count:
                        is_positive = random.random() < 0.6
                    else:
                        is_positive = random.random() > 0.5
                    
                    literal = var if is_positive else -var
                    clause.append(literal)
            else:
                # 变量不够，随机选择全部变量
                clause_vars = random.sample(range(1, num_vars + 1), clause_length)
                
                # 决定每个变量的正负性
                clause = []
                for var in clause_vars:
                    if var == sat_var:
                        # 使用预分配值
                        is_positive = sat_value
                    else:
                        pos_count = var_occurrence[var]['pos']
                        neg_count = var_occurrence[var]['neg']
                        
                        # 基于出现频率平衡正负
                        if pos_count > neg_count:
                            is_positive = random.random() > 0.6
                        elif neg_count > pos_count:
                            is_positive = random.random() < 0.6
                        else:
                            is_positive = random.random() > 0.5
                    
                    literal = var if is_positive else -var
                    clause.append(literal)
        else:
            # 常规情况，尝试基于变量出现频率选择变量
            var_freq = [(var, var_occurrence[var]['pos'] + var_occurrence[var]['neg']) 
                      for var in range(1, num_vars + 1)]
            var_freq.sort(key=lambda x: x[1])  # 按出现频率排序
            
            # 引入随机性并优先选择出现频率低的变量
            if num_vars >= clause_length * 2:
                candidate_vars = [v[0] for v in var_freq[:max(num_vars//2, clause_length*2)]]
                clause_vars = random.sample(candidate_vars, clause_length)
            else:
                clause_vars = random.sample(range(1, num_vars + 1), clause_length)
            
            # 决定每个变量的正负性
            clause = []
            for var in clause_vars:
                # 检查是否为预分配变量
                if var in assigned_vars:
                    # 50%概率使用预分配值，50%概率随机
                    if random.random() < 0.5:
                        is_positive = assigned_vars[var]
                    else:
                        pos_count = var_occurrence[var]['pos']
                        neg_count = var_occurrence[var]['neg']
                        
                        if pos_count > neg_count:
                            is_positive = random.random() > 0.6
                        elif neg_count > pos_count:
                            is_positive = random.random() < 0.6
                        else:
                            is_positive = random.random() > 0.5
                else:
                    pos_count = var_occurrence[var]['pos']
                    neg_count = var_occurrence[var]['neg']
                    
                    if pos_count > neg_count:
                        is_positive = random.random() > 0.6
                    elif neg_count > pos_count:
                        is_positive = random.random() < 0.6
                    else:
                        is_positive = random.random() > 0.5
                
                literal = var if is_positive else -var
                clause.append(literal)
        
        # 确保不是全正或全负的子句
        all_pos = all(lit > 0 for lit in clause)
        all_neg = all(lit < 0 for lit in clause)
        
        if (all_pos or all_neg) and clause_length > 1 and random.random() < 0.8:
            # 80%的概率翻转一个变量
            flip_idx = random.randint(0, clause_length - 1)
            clause[flip_idx] = -clause[flip_idx]
        
        # 更新变量出现次数统计
        for lit in clause:
            var = abs(lit)
            if lit > 0:
                var_occurrence[var]['pos'] += 1
            else:
                var_occurrence[var]['neg'] += 1
        
        clause_str = " ".join(map(str, clause)) + " 0"
        lines.append(clause_str)
    
    return "\n".join(lines)

def run_solver(dimacs_input, solver_path, is_exe=False):
    """
    运行SAT求解器并返回结果
    
    Args:
        dimacs_input: DIMACS格式的输入字符串
        solver_path: 求解器路径
        is_exe: 是否为可执行文件
    
    Returns:
        (result, output) - result为"SATISFIABLE"或"UNSATISFIABLE"，output为完整输出
    """
    if is_exe:
        # 对于可执行文件，通过管道传入输入
        process = subprocess.Popen(
            [solver_path], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, error = process.communicate(input=dimacs_input)
    else:
        # 对于Python脚本，使用python命令运行
        process = subprocess.Popen(
            ["python", solver_path], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output, error = process.communicate(input=dimacs_input)
    
    # 查找结果行
    for line in output.splitlines():
        if line.startswith("s "):
            result = line[2:].strip()
            # 简化结果显示
            if "SATISFIABLE" in result:
                result = "SAT" if "UN" not in result else "UNSAT"
            return result, output
    
    return "ERROR", output + "\nERROR: " + error

def save_wrong_case(dimacs_input, output1, output2, case_number):
    """
    保存不一致的测试用例
    
    Args:
        dimacs_input: DIMACS格式输入
        output1: 第一个求解器的输出
        output2: 第二个求解器的输出
        case_number: 测试用例编号
    """
    # 确保WRONG目录存在
    wrong_dir = Path("WRONG")
    wrong_dir.mkdir(exist_ok=True)
    
    # 保存输入
    with open(wrong_dir / f"case_{case_number}_input.cnf", "w") as f:
        f.write(dimacs_input)
    
    # 保存输出
    with open(wrong_dir / f"case_{case_number}_output_solver.txt", "w") as f:
        f.write(output1)
    
    with open(wrong_dir / f"case_{case_number}_output_bf.txt", "w") as f:
        f.write(output2)

def main():
    # 使用Path设置求解器路径
    current_dir = Path(__file__).parent
    solver_path = current_dir / "solver.py"
    bf_solver_path = current_dir / "bf_SATsolver.exe"
    
    # 确保路径存在
    if not solver_path.exists() or not bf_solver_path.exists():
        print(f"错误：求解器路径不存在。请检查：\n{solver_path}\n{bf_solver_path}")
        return
    
    # 测试参数初始化
    initial_vars = 0     # 初始变量数
    max_vars = 100       # 最大变量数
    max_clauses = 600    # 最大子句数
    
    # 测试统计
    total_tests = 0
    passed_tests = 0
    wrong_cases = 0
    
    # 新策略：子句数量与循环次数相同，变量数每4个循环增加一次
    num_vars = initial_vars
    loop_count = 0
    
    print("开始测试...")
    print("循环次数 | 变量数 | 原始子句数 | 实际子句数 | solver结果 | bf_solver结果 | 一致性 | 求解时间")
    print("-" * 90)
    
    # 循环测试，按新规则增加变量和子句数量
    while loop_count <= max_clauses or num_vars <= max_vars:
        loop_count += 1
        num_clauses = loop_count
        
        # 每4次循环，变量数增加1
        if loop_count % 4 == 0:
            num_vars += 1
        
        start_time = time.time()
        
        # 生成随机CNF公式
        dimacs_input = generate_random_cnf(num_vars, num_clauses)
        
        # 从生成的DIMACS中获取实际子句数
        actual_clauses = 0
        for line in dimacs_input.splitlines():
            if line.startswith("p cnf"):
                parts = line.split()
                if len(parts) >= 4:
                    actual_clauses = int(parts[3])
                break
        
        # 运行两个求解器
        result1, output1 = run_solver(dimacs_input, str(solver_path), is_exe=False)
        result2, output2 = run_solver(dimacs_input, str(bf_solver_path), is_exe=True)
        
        end_time = time.time()
        solve_time = end_time - start_time
        
        # 检查结果是否一致
        total_tests += 1
        if result1 == result2:
            passed_tests += 1
            result_str = "通过"
        else:
            wrong_cases += 1
            result_str = "不一致"
            save_wrong_case(dimacs_input, output1, output2, wrong_cases)
        
        print(f"{loop_count:8d} | {num_vars:6d} | {num_clauses:10d} | {actual_clauses:10d} | {result1:10s} | {result2:13s} | {result_str:4s} | {solve_time:.2f}s")
        
    # 输出统计结果
    pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print("\n测试完成！")
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"不一致案例: {wrong_cases}")
    print(f"通过率: {pass_rate:.2f}%")
    
    if wrong_cases > 0:
        print(f"\n不一致的案例已保存到 WRONG 文件夹中。")

if __name__ == "__main__":
    main()
