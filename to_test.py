import random
import subprocess
import os
import time
from pathlib import Path

def generate_random_cnf(num_vars, num_clauses):
    """
    生成随机CNF公式的DIMACS格式字符串
    
    子句长度概率分布:
    - 长度为1的概率: 0.01
    - 长度为2的概率: 0.30
    - 长度为3的概率: 0.69
    
    Args:
        num_vars: 变量数量
        num_clauses: 子句数量
    
    Returns:
        DIMACS格式的CNF公式字符串
    """
    lines = [f"p cnf {num_vars} {num_clauses}"]
    
    for _ in range(num_clauses):
        # 根据指定概率选择子句长度
        rand = random.random()
        if rand < 0.01:
            clause_length = 1
        elif rand < 0.31:  # 0.01 + 0.30
            clause_length = 2
        else:
            clause_length = 3
        
        # 确保子句长度不超过可用变量数
        clause_length = min(clause_length, num_vars)
        
        # 随机选择变量并决定是否取反
        clause_vars = random.sample(range(1, num_vars + 1), clause_length)
        clause = [var if random.random() > 0.5 else -var for var in clause_vars]
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
            return line[2:].strip(), output
    
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
    print("循环次数 | 变量数 | 子句数 | 结果 | 求解时间")
    print("-" * 50)
    
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
        
        print(f"{loop_count:8d} | {num_vars:6d} | {num_clauses:6d} | {result_str:1s} | {solve_time:.2f}s")
        
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
