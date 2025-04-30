#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <chrono>

using namespace std;

// 表示一个SAT问题
struct SATproblem {
    int numVars;                       
    vector<vector<int>> clauses;       
};

/**
 * 从DIMACS格式解析SAT问题
 * 假设输入可能有空子句，但不会有其他不规范情况
 */
SATproblem parseDIMACS() {
    SATproblem problem;
    problem.numVars = 0;
    string line;
    int numClauses = 0;
    bool headerFound = false;
    
    while (getline(cin, line)) {
        if (line.empty()) continue;
        
        if (line[0] == 'c') {
            continue; // 注释行
        }
        else if (line[0] == 'p') {
            istringstream iss(line);
            string p, cnf;
            iss >> p >> cnf >> problem.numVars >> numClauses;
            headerFound = true;
        }
        else {
            if (!headerFound) continue;
            
            istringstream iss(line);
            vector<int> clause;
            int lit;
            while (iss >> lit && lit != 0) {
                int var = abs(lit);
                if (var > problem.numVars) {
                    problem.numVars = var;
                }
                clause.push_back(lit);
            }
            
            // 移除重复文字并检查互补文字
            sort(clause.begin(), clause.end());
            auto last = unique(clause.begin(), clause.end());
            clause.erase(last, clause.end());
            
            bool tautology = false;
            for (size_t i = 0; i < clause.size() - 1; i++) {
                if (clause[i] == -clause[i+1]) {
                    tautology = true;
                    break;
                }
            }
            
            if (!tautology) {
                problem.clauses.push_back(clause);
            }
        }
    }
    
    return problem;
}

/**
 * 检查当前赋值是否导致某个子句冲突
 * 如果有任何子句中的所有文字都不满足，则返回true
 */
bool checkConflict(const SATproblem& problem, const vector<int>& assignment) {
    for (const auto& clause : problem.clauses) {
        bool satisfied = false;
        bool undecided = false;
        
        for (int lit : clause) {
            int var = abs(lit);
            if (var > assignment.size()) {
                undecided = true;
                break;
            }
            
            int value = assignment[var-1];
            
            if (value == 0) {
                undecided = true;
                break; // 优化：有未赋值变量则直接跳到下一子句
            }
            
            if ((lit > 0 && value > 0) || (lit < 0 && value < 0)) {
                satisfied = true;
                break;
            }
        }
        
        // 如果子句中所有文字都已赋值且都不满足，则冲突
        if (!satisfied && !undecided) {
            return true; // 存在冲突
        }
    }
    
    return false;  // 没有冲突
}

/**
 * 寻找单子句（只有一个未赋值的文字）
 * 返回所有单子句中的文字列表
 */
vector<int> findUnitClauses(const SATproblem& problem, const vector<int>& assignment) {
    vector<int> unitLiterals;
    
    for (const auto& clause : problem.clauses) {
        int unassignedLit = 0;
        bool satisfied = false;
        
        for (int lit : clause) {
            int var = abs(lit);
            int value = assignment[var-1];
            
            if ((lit > 0 && value > 0) || (lit < 0 && value < 0)) {
                satisfied = true;
                break;
            }
            
            if (value == 0) {
                if (unassignedLit != 0) {
                    unassignedLit = 0;
                    break;
                }
                unassignedLit = lit;
            }
        }
        
        if (!satisfied && unassignedLit != 0) {
            unitLiterals.push_back(unassignedLit);
        }
    }
    
    return unitLiterals;
}

/**
 * 寻找纯文字（在所有未满足子句中只以一种极性出现的文字）
 * 返回所有纯文字列表
 */
vector<int> findPureLiterals(const SATproblem& problem, const vector<int>& assignment) {
    vector<bool> posAppears(problem.numVars + 1, false);
    vector<bool> negAppears(problem.numVars + 1, false);
    vector<int> pureLiterals;
    
    for (const auto& clause : problem.clauses) {
        bool satisfied = false;
        
        for (int lit : clause) {
            int var = abs(lit);
            int value = assignment[var-1];
            
            if ((lit > 0 && value > 0) || (lit < 0 && value < 0)) {
                satisfied = true;
                break;
            }
        }
        
        if (!satisfied) {
            for (int lit : clause) {
                int var = abs(lit);
                int value = assignment[var-1];
                
                if (value == 0) {
                    if (lit > 0) {
                        posAppears[var] = true;
                    } else {
                        negAppears[var] = true;
                    }
                }
            }
        }
    }
    
    for (int var = 1; var <= problem.numVars; var++) {
        if (assignment[var-1] == 0) {
            if (posAppears[var] && !negAppears[var]) {
                pureLiterals.push_back(var);
            } else if (!posAppears[var] && negAppears[var]) {
                pureLiterals.push_back(-var);
            }
        }
    }
    
    return pureLiterals;
}

/**
 * 递归尝试所有可能的赋值
 * 使用单子句传播和纯文字消除优化搜索过程
 */
bool solve(const SATproblem& problem, vector<int>& assignment, int varIndex) {
    if (checkConflict(problem, assignment)) {
        return false;
    }
    
    // 单子句传播
    vector<int> unitLiterals = findUnitClauses(problem, assignment);
    vector<pair<int, int>> saved; // 记录变更以便回溯
    
    for (int lit : unitLiterals) {
        int var = abs(lit);
        if (assignment[var-1] == 0) {
            saved.push_back({var-1, 0});
            assignment[var-1] = (lit > 0) ? 1 : -1;
            
            if (checkConflict(problem, assignment)) {
                for (auto& p : saved) {
                    assignment[p.first] = p.second;
                }
                return false;
            }
        }
    }
    
    // 纯文字消除
    vector<int> pureLiterals = findPureLiterals(problem, assignment);
    for (int lit : pureLiterals) {
        int var = abs(lit);
        if (assignment[var-1] == 0) {
            saved.push_back({var-1, 0});
            assignment[var-1] = (lit > 0) ? 1 : -1;
        }
    }
    
    if (varIndex > problem.numVars) {
        return !checkConflict(problem, assignment);
    }
    
    int nextVar = varIndex;
    while (nextVar <= problem.numVars && assignment[nextVar-1] != 0) {
        nextVar++;
    }
    
    if (nextVar > problem.numVars) {
        return !checkConflict(problem, assignment);
    }
    
    // 尝试将变量赋值为真
    assignment[nextVar-1] = 1;
    if (solve(problem, assignment, nextVar+1)) {
        return true;
    }
    
    // 尝试将变量赋值为假
    assignment[nextVar-1] = -1;
    if (solve(problem, assignment, nextVar+1)) {
        return true;
    }
    
    // 恢复本次递归中所做的所有赋值
    assignment[nextVar-1] = 0;
    for (auto& p : saved) {
        assignment[p.first] = p.second;
    }
    
    return false;
}

int main() {
    try {
        SATproblem problem = parseDIMACS();
        
        if (problem.numVars <= 0) {
            cout << "s ERROR" << endl;
            return 1;
        }
        
        vector<int> assignment(problem.numVars, 0);
        
        bool result = solve(problem, assignment, 1);
        
        if (result) {
            cout << "s SATISFIABLE" << endl;
            cout << "v ";
            for (int i = 0; i < problem.numVars; i++) {
                cout << (assignment[i] * (i+1)) << " ";
            }
            cout << "0" << endl;
        } else {
            cout << "s UNSATISFIABLE" << endl;
        }
    } catch (const exception& e) {
        cerr << "Exception: " << e.what() << endl;
        cout << "s ERROR" << endl;
    } catch (...) {
        cerr << "Unknown exception occurred" << endl;
        cout << "s ERROR" << endl;
    }
    
    return 0;
}
