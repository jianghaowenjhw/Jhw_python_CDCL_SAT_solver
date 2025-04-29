import sys
from typing import List, Tuple, Optional

class SATSolver:
    def __init__(self, debug_output: int = 0) -> None:
        """
        初始化SAT求解器. 
        
        Args:
            debug_output: 调试输出级别, 0表示不输出调试信息
        """
        self.debug = debug_output
        self.clauses = []         # 存储所有子句(包括学习的新子句)
        self.var_info = {}        # 变量信息：值、决策层级、原因子句
        self.decision_level = 0    # 当前决策层级
        self.trail = []            # 赋值栈, 按顺序记录赋值操作
        self.trail_lim = []        # 记录每个决策层级的起始位置
        self.var_order = []        # 变量选择顺序

    def parse_dimacs(self) -> bool:
        """
        初始化，解析DIMACS格式输入
        
        Returns:
            如果输入有效返回True，如果发现空子句返回False
        """
        for line in sys.stdin:
            line = line.strip()
            if line.startswith('c') or not line:
                continue
            if line.startswith('p cnf'):
                _, _, n_vars, _ = line.split()
                self.var_order = list(range(1, int(n_vars)+1))
                continue
            clause = [int(x) for x in line.split()[:-1]]
            if not clause:  # 检测到空子句
                self.debug_print("Empty clause detected")
                return False
            self.clauses.append(clause)
            self.debug_print(f"Parsed clause: {clause}")
        return True

    def debug_print(self, message: str) -> None:
        """
        打印调试信息. 
        
        Args:
            message: 要打印的调试信息
        """
        if self.debug:
            print(message)

    def assign(self, var: int, value: bool, reason_list: Optional[List[int]] = None) -> None:
        """
        给变量赋值. 
        
        Args:
            var: 要赋值的变量编号
            value: 赋给变量的布尔值
            reason_clause: 导致此赋值的原因变量构成的列表, 若为决策变量则为None
        """
        self.var_info[var] = {
            'value': value,
            'decision_level': self.decision_level,
            'reason': reason_list
        }
        self.trail.append(var)
        self.debug_print(f"Assign: {var} = {value} (DL: {self.decision_level}, Reason: {reason_list})")

    def unassign(self, var: int) -> None: 
        """
        在self.info中取消变量的赋值. 
        
        Args:
            var: 要取消赋值的变量编号
        """
        if var in self.var_info:
            del self.var_info[var]

    def unit_propagation(self) -> bool:
        """
        执行一步单元传播过程. 
        
        查找单元子句并为其中的变量赋值, 一次只传播一个变量. 
        
        Returns:
            如果成功传播一个变量返回True, 否则返回False
        """
        for clause in self.clauses:
            unassigned = []
            is_satisfied = False
            for lit in clause:
                var = abs(lit)
                if var not in self.var_info:
                    unassigned.append(lit)
                else:
                    if (lit > 0 and self.var_info[var]['value']) or (lit < 0 and not self.var_info[var]['value']):
                        is_satisfied = True
                        break
            if is_satisfied:
                continue
            if len(unassigned) == 1:
                lit = unassigned[0]
                var = abs(lit)
                value = (lit > 0)
                # 原因列表: 逼迫这个变量赋值的其他变量, 为UP子句中的其他变量. 特别地, 单变量作为子句是, 原因列表是空列表. 
                reason_list = [abs(l) for l in clause if abs(l) != var]
                self.assign(var, value, reason_list)
                self.debug_print(f"Unit propagation: {var} = {value} from clause {clause}, reason: {reason_list}")
                return True
        return False

    def check_conflict(self) -> Optional[List[int]]:
        """
        检查是否存在冲突的子句. 
        
        遍历所有子句, 检查是否有完全不满足的子句(冲突). 
        
        Returns:
            发生冲突的子句, 如果没有冲突则返回None
        """
        for clause in self.clauses:
            clause_unsat = True
            for lit in clause:
                var = abs(lit)
                if var not in self.var_info:
                    clause_unsat = False
                    break
                if (lit > 0 and self.var_info[var]['value']) or (lit < 0 and not self.var_info[var]['value']):
                    clause_unsat = False
                    break
            if clause_unsat:
                self.debug_print(f"Conflict detected in clause: {clause}")
                return clause
        return None

    def learn_clause(self, conflict_clause: List[int]) -> List[int]:
        """
        从冲突中学习新子句. 
        
        从冲突子句开始, 通过替换非决策变量来生成学习子句. 
        
        Args:
            conflict_clause: 发生冲突的子句
            
        Returns:
            学习到的新子句, 如果无法解决冲突则返回None
        """

        conflict_vars = [abs(lit) for lit in conflict_clause]
        self.debug_print(f"vars in clause: {conflict_vars}")

        # 循环替换非决策变量
        while True:
            need_to_replace = False

            for var in list(conflict_vars):
                if var in self.var_info and not (self.var_info[var]['reason'] is None):
                    need_to_replace = True
                    conflict_vars.remove(var)

                    reason_vars = [abs(lit) for lit in self.var_info[var]['reason']]

                    for reason_var in reason_vars:
                        if reason_var not in conflict_vars:
                            conflict_vars.append(reason_var)
            
            if not need_to_replace:
                break
        
        # 从循环处理后的原因列表中学习新子句
        learned_clause = []
        for var in conflict_vars:
            if self.var_info[var]['value']:
                learned_clause.append(-var)
            else:
                learned_clause.append(var)

        learned_clause.sort(key=abs)
        self.debug_print(f"Learned clause: {learned_clause}")

        return learned_clause

    def determine_backtrack_level(self, learned_clause: List[int]) -> int:
        """
        根据学习子句计算需要回溯的决策层级. 

        是学习子句中第二高的决策层级.
        
        Args:
            learned_clause: 学习到的子句
            
        Returns:
            需要回溯到的决策层级
        """
        decision_levels = []
        for lit in learned_clause:
            var = abs(lit)
            if var in self.var_info:
                decision_levels.append(self.var_info[var]['decision_level'])
        
        decision_levels = sorted(decision_levels)
        
        if len(decision_levels) <= 1:
            return 0
        
        back_level = decision_levels[-2]
        
        self.debug_print(f"Back to Decision Level : {back_level}")
        return back_level

    def analyze_conflict(self, conflict_clause: List[int]) -> Tuple[List[int], int]:
        """
        分析冲突, 产生学习子句并确定回溯层级. 
        
        根据冲突子句学习新的子句, 找到根本原因并确定回溯层级. 
        
        Args:
            conflict_clause: 发生冲突的子句
            
        Returns:
            元组(学习子句, 回溯层级)
        """
        learned_clause = self.learn_clause(conflict_clause)
            
        back_level = self.determine_backtrack_level(learned_clause)
        
        return learned_clause, back_level

    def backtrack(self, level: int) -> None:
        """
        回溯到指定的决策层级. 
        
        撤销所有高于指定层级的变量赋值. 
        
        Args:
            level: 要回溯到的决策层级
        """
        while self.decision_level > level:
            self.decision_level -= 1
            pos = self.trail_lim.pop()
            for var in self.trail[pos:]:
                self.unassign(var)
            self.trail = self.trail[:pos]

    def pick_variable(self) -> Optional[int]:
        """
        选择下一个决策变量. 
        
        从未赋值的变量中选择一个作为下一个决策变量. 
        
        Returns:
            选择的变量编号, 如果所有变量都已赋值则返回None
        """
        for var in self.var_order:
            if var not in self.var_info:
                return var
        return None

    def cdcl(self) -> str:
        """
        执行冲突驱动的子句学习(CDCL)算法. 
        
        实现CDCL主循环, 包括冲突检查、单元传播、冲突分析、回溯和决策变量选择. 
        
        Returns:
            "SAT"表示可满足, "UNSAT"表示不可满足
        """
        self.decision_level = 0
        self.trail_lim = []
        
        while True:
            conflict_clause = self.check_conflict()
            if conflict_clause is not None:
                if self.decision_level == 0:
                    return "UNSAT"
                
                analysis_result = self.analyze_conflict(conflict_clause)
                learned_clause, back_level = analysis_result
                if not learned_clause:
                    return "UNSAT"
                
                self.debug_print(f"Learned clause: {learned_clause}")
                self.debug_print(f"Backtrack to level: {back_level}")
                self.clauses.append(learned_clause)
                self.backtrack(back_level)
                continue
            
            propagated = self.unit_propagation()
            if propagated:
                continue
            
            if len(self.var_info) == len(self.var_order):
                return "SAT"
                
            var = self.pick_variable()
            if var is None:
                return "SAT"
                
            self.decision_level += 1
            self.trail_lim.append(len(self.trail))
            self.assign(var, True, None)

    def solve(self) -> None:
        """
        解决SAT问题并输出结果. 
        
        解析输入, 执行CDCL算法, 并以标准格式输出结果. 
        """
        if not self.parse_dimacs():
            print("s ERROR")
            return
            
        result = self.cdcl()
        print("s SATISFIABLE" if result == "SAT" else "s UNSATISFIABLE")
        if result == "SAT":
            print("v", end="")
            for var in self.var_order:
                print(f" {var if self.var_info[var]['value'] else -var}", end="")
            print(" 0")

if __name__ == "__main__":
    debug = 1 if "--debug" in sys.argv else 0
    solver = SATSolver(debug_output=debug)
    solver.solve()