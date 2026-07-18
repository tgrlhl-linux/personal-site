#!/bin/bash
# ============================================================
#   Linux 作业五 —— 成绩管理系统 (Shell 实现)
#   学号尾数 1/4/7/0  题目一
#   ★ 加分：学院/班级维度 + 三级权限 + 报表导出
# ============================================================

# ---------- 全局配置 ----------
DATA_FILE="${DATA_FILE:-$HOME/work5/data/scores_utf8.csv}"
DATA_BAK="${DATA_FILE}.bak"
ORIGINAL_DATA="${ORIGINAL_DATA:-$HOME/work5/data/作业五题目一数据.csv}"
CLASS_FILE="${CLASS_FILE:-$HOME/work5/data/class_info.txt}"
REPORT_DIR="${REPORT_DIR:-$HOME/work5/report}"
USER_FILE="${USER_FILE:-$HOME/work5/data/users.txt}"
SESSION_USER=""
SESSION_ROLE=""
SESSION_SCOPE=""   # * = admin全权限 | class1,class2 = teacher管辖班级 | 学号 = student本人

# ---------- 颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# ---------- 工具函数 ----------
awk_add() { awk "BEGIN { printf \"%.2f\", $1 + $2; exit }"; }
awk_mul() { awk "BEGIN { printf \"%.2f\", $1 * $2; exit }"; }
awk_div() { awk "BEGIN { printf \"%.2f\", $1 / $2; exit }"; }
awk_ge()  { awk "BEGIN { if ($1 >= $2) print 1; else print 0; exit }"; }
awk_gt()  { awk "BEGIN { if ($1 > $2) print 1; else print 0; exit }"; }
awk_lt()  { awk "BEGIN { if ($1 < $2) print 1; else print 0; exit }"; }

# 报告输出（同时显示和写文件）
report_out() {
    local file="$1"
    shift
    mkdir -p "$REPORT_DIR"
    echo "$@" | tee -a "$file"
}
report_printf() {
    local file="$1"
    local fmt="$2"
    shift 2
    printf "$fmt" "$@" | tee -a "$file"
}

# ---------- 数据初始化 ----------
init_data() {
    if [[ ! -f "$DATA_FILE" ]]; then
        if [[ -f "$ORIGINAL_DATA" ]]; then
            echo -e "${YELLOW}正在转换原始数据为 UTF-8 ...${NC}"
            iconv -f GBK -t UTF-8 "$ORIGINAL_DATA" -o "$DATA_FILE" 2>/dev/null
            [[ $? -ne 0 ]] && { echo -e "${RED}转换失败${NC}"; exit 1; }
            cp "$DATA_FILE" "$DATA_BAK"
            echo -e "${GREEN}数据初始化完成，共 $(tail -n +2 "$DATA_FILE" | wc -l) 条记录${NC}"
        else
            echo -e "${RED}找不到原始数据文件 $ORIGINAL_DATA${NC}"
            exit 1
        fi
    fi
    sed -i 's/\r$//' "$DATA_FILE" 2>/dev/null
}

# ---------- 班级配置文件初始化 ----------
declare -A student_class    # 学号 → 班级
declare -A class_college    # 班级 → 学院
declare -A class_dept       # 班级 → 系

init_class_info() {
    if [[ ! -f "$CLASS_FILE" ]]; then
        echo -e "${YELLOW}未检测到班级配置文件，正在自动生成...${NC}"
        cat > "$CLASS_FILE" << 'EOF'
# 班级配置
# 格式：班级名称 | 学院 | 系
计科1801 | 信息科学与工程学院 | 计算机科学系
计科1802 | 信息科学与工程学院 | 计算机科学系
软件1801 | 信息科学与工程学院 | 软件工程系
软件1802 | 信息科学与工程学院 | 软件工程系
网工1801 | 信息科学与工程学院 | 网络工程系
人工1801 | 信息科学与工程学院 | 人工智能系
EOF
        echo -e "${GREEN}班级模板已创建: $CLASS_FILE${NC}"
        echo -e "${YELLOW}已按学号尾数自动分配: 0-1→计科1801  2-3→计科1802  4-5→软件1801${NC}"
        echo -e "${YELLOW}            6-7→软件1802  8→网工1801  9→人工1801${NC}"
    fi

    # 读取班级配置
    while IFS='|' read -r cls clg dept; do
        cls=$(echo "$cls" | xargs)
        clg=$(echo "$clg" | xargs)
        dept=$(echo "$dept" | xargs)
        [[ -z "$cls" || "$cls" == \#* ]] && continue
        class_college["$cls"]="$clg"
        class_dept["$cls"]="$dept"
    done < "$CLASS_FILE"

    # 按学号尾数分配班级
    while IFS= read -r line; do
        local sid
        sid=$(echo "$line" | awk -F',' '{print $1}')
        [[ -z "$sid" || "$sid" == "学号" ]] && continue
        local last_digit=${sid: -1}
        local class_name=""
        case $last_digit in
            0|1) class_name="计科1801" ;;
            2|3) class_name="计科1802" ;;
            4|5) class_name="软件1801" ;;
            6|7) class_name="软件1802" ;;
            8)   class_name="网工1801" ;;
            9)   class_name="人工1801" ;;
        esac
        student_class["$sid"]="$class_name"
    done < <(tail -n +2 "$DATA_FILE")
}

# ---------- 用户认证系统（三级权限） ----------
init_users() {
    if [[ ! -f "$USER_FILE" ]]; then
        cat > "$USER_FILE" << 'EOF'
# 用户文件  格式: 用户名|密码|角色(admin/teacher/student)|数据范围
# admin   → *                          （全部数据）
# teacher → 计科1801,计科1802          （管辖班级，逗号分隔）
# student → 2018182811                 （本人学号）
admin|admin123|admin|*
zhanglao|123456|teacher|计科1801,计科1802
wanglao|123456|teacher|软件1801,软件1802
EOF
        echo -e "${GREEN}用户文件已创建: $USER_FILE${NC}"
        echo -e "${YELLOW}默认管理员: admin / admin123${NC}"
        echo -e "${YELLOW}教师账号: zhanglao(计科1801/1802) / wanglao(软件1801/1802)${NC}"
    fi
}

do_login() {
    local max_attempts=3
    for ((attempt=1; attempt<=max_attempts; attempt++)); do
        echo ""
        echo -e "${CYAN}===== 用户登录 =====${NC}"
        read -p "用户名: " username
        read -s -p "密码: " password
        echo ""

        local stored_pass stored_role stored_scope
        stored_pass=$(grep "^$username|" "$USER_FILE" 2>/dev/null | awk -F'|' '{print $2}')
        stored_role=$(grep "^$username|" "$USER_FILE" 2>/dev/null | awk -F'|' '{print $3}' | tr -d ' \r\n')
        stored_scope=$(grep "^$username|" "$USER_FILE" 2>/dev/null | awk -F'|' '{print $4}' | tr -d ' \r\n')

        if [[ "$password" == "$stored_pass" && -n "$stored_role" ]]; then
            SESSION_USER="$username"
            SESSION_ROLE="$stored_role"
            SESSION_SCOPE="$stored_scope"
            echo -e "${GREEN}登录成功！欢迎 $username (${stored_role})${NC}"

            # 显示用户数据范围提示
            local scope_desc=""
            case "$SESSION_ROLE" in
                admin)    scope_desc="拥有全部数据权限" ;;
                teacher)  scope_desc="管辖班级: $SESSION_SCOPE" ;;
                student)  scope_desc="本人学号: $SESSION_SCOPE" ;;
            esac
            echo -e "${YELLOW}数据范围: $scope_desc${NC}"
            return 0
        else
            echo -e "${RED}用户名或密码错误！剩余尝试次数: $((max_attempts - attempt))${NC}"
        fi
    done
    echo -e "${RED}登录失败，退出系统${NC}"
    exit 1
}

# ---------- 获取学生组织信息 ----------
get_student_class() {
    local sid="$1"
    echo "${student_class[$sid]:-未分配}"
}

get_class_college() {
    local cls="$1"
    echo "${class_college[$cls]:-未知学院}"
}

get_class_dept() {
    local cls="$1"
    echo "${class_dept[$cls]:-未知系}"
}

# ---------- 成绩/学分工具函数 ----------
grade_to_num() {
    local g="$1"
    case "$g" in
        优秀|优)  echo 95 ;;
        良好|良)  echo 85 ;;
        中等|中)  echo 75 ;;
        及格|及)  echo 65 ;;
        不及格)   echo 55 ;;
        */[0-9]*)
            local first="${g%%/*}"
            grade_to_num "$first"
            ;;
        [0-9]*)
            echo "$g" | grep -oE '^[0-9]+(\.[0-9]+)?' | head -1
            ;;
        *) echo "" ;;
    esac
}

get_header() { head -1 "$DATA_FILE"; }

extract_credit() {
    local course="$1"
    echo "$course" | grep -oP '\[\K[0-9]*(\.[0-9]+)?' | head -1
}

get_numeric_at_col() {
    local line="$1" col="$2"
    local raw; raw=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
    grade_to_num "$raw"
}

calc_stats_for_line() {
    local line="$1"
    local total=0 count=0
    local nf; nf=$(echo "$line" | awk -F',' '{print NF}')
    for ((i=3; i<=nf; i++)); do
        local val; val=$(get_numeric_at_col "$line" "$i")
        if [[ -n "$val" ]]; then
            total=$(awk_add "$total" "$val")
            count=$((count + 1))
        fi
    done
    if [[ $count -gt 0 ]]; then
        local avg; avg=$(awk_div "$total" "$count")
        echo "$total|$count|$avg"
    else
        echo "0|0|0"
    fi
}

# awk 版的成绩转数值函数（给 awk 脚本用）
get_toNum_awk() {
    cat << 'AWK'
    function toNum(v) {
        if (v == "优秀" || v == "优") return 95
        if (v == "良好" || v == "良") return 85
        if (v == "中等" || v == "中") return 75
        if (v == "及格" || v == "及") return 65
        if (v == "不及格") return 55
        if (index(v, "/")) { sub(/\/.*$/, "", v); return toNum(v) }
        gsub(/[^0-9.]/, "", v)
        if (v == "") return -1
        return v + 0
    }
AWK
}

# ---------- 用户数据隔离 ----------
# 返回当前用户有权访问的数据行（不含表头）
get_data_lines() {
    local all_data
    all_data=$(tail -n +2 "$DATA_FILE")
    [[ -z "$all_data" ]] && return

    case "$SESSION_ROLE" in
        admin)
            echo "$all_data"
            ;;
        teacher)
            local allowed_classes=",$SESSION_SCOPE,"
            local line sid scls
            while IFS= read -r line; do
                sid=$(echo "$line" | awk -F',' '{print $1}')
                scls="${student_class[$sid]:-}"
                [[ -z "$scls" ]] && continue
                if echo "$allowed_classes" | grep -q ",$scls,"; then
                    echo "$line"
                fi
            done <<< "$all_data"
            ;;
        student)
            grep "^$SESSION_SCOPE," <<< "$all_data" 2>/dev/null || true
            ;;
    esac
}

# 检查老师是否有权限操作该学号
teacher_can_manage_sid() {
    local sid="$1"
    local scls="${student_class[$sid]:-}"
    [[ -z "$scls" ]] && return 1
    local allowed_classes=",$SESSION_SCOPE,"
    echo "$allowed_classes" | grep -q ",$scls,"
}

# =============================================================
#  基本功能：增删改查 + 排序
# =============================================================

add_student() {
    echo -e "${CYAN}===== 添加学生成绩 =====${NC}"
    read -p "请输入学号: " sid
    grep -q "^$sid," "$DATA_FILE" 2>/dev/null && { echo -e "${RED}学号 $sid 已存在！${NC}"; return; }
    # 老师只能添加属于其管辖班级的学生
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        local scls="${student_class[$sid]:-未知}"
        echo -e "${RED}权限不足！学号尾数对应的班级「$scls」不在您的管辖范围内。${NC}"
        echo -e "${YELLOW}您的管辖班级: $SESSION_SCOPE${NC}"
        return
    fi
    read -p "请输入姓名: " name
    echo -e "${YELLOW}请依次输入各科成绩（留空表示缺考）:${NC}"
    local header; header=$(get_header)
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    local new_line="$sid,$name"
    for ((i=3; i<=nf; i++)); do
        local fn; fn=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        read -p "  [$fn]: " score
        new_line="$new_line,$score"
    done
    echo "$new_line" >> "$DATA_FILE"
    echo -e "${GREEN}添加成功！${NC}"
}

delete_student() {
    echo -e "${CYAN}===== 删除学生成绩 =====${NC}"
    read -p "请输入要删除的学号: " sid
    grep -q "^$sid," "$DATA_FILE" 2>/dev/null || { echo -e "${RED}学号 $sid 不存在！${NC}"; return; }
    # 老师只能删除管辖班级的学生
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        echo -e "${RED}权限不足！该学生不属于您管辖的班级。${NC}"
        return
    fi
    echo -e "${YELLOW}找到以下记录:${NC}"
    grep "^$sid," "$DATA_FILE"
    read -p "确认删除？(y/n): " confirm
    if [[ "$confirm" == [yY] ]]; then
        sed -i "/^$sid,/d" "$DATA_FILE" && echo -e "${GREEN}删除成功！${NC}"
    else
        echo -e "${YELLOW}已取消${NC}"
    fi
}

modify_score() {
    echo -e "${CYAN}===== 修改成绩 =====${NC}"
    read -p "请输入学号: " sid
    local line; line=$(grep "^$sid," "$DATA_FILE" 2>/dev/null)
    [[ -z "$line" ]] && { echo -e "${RED}学号 $sid 不存在！${NC}"; return; }
    # 老师只能修改管辖班级的学生
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        echo -e "${RED}权限不足！该学生不属于您管辖的班级。${NC}"
        return
    fi
    local header; header=$(get_header)
    echo -e "\n${YELLOW}当前记录:${NC}"
    echo "$header" | awk -F',' '{for(i=1;i<=NF;i++) printf "%-3d %-25s\n", i, $i}'
    echo ""
    echo "$line" | awk -F',' '{for(i=1;i<=NF;i++) printf "%-3d %-25s\n", i, $i}'
    read -p "请输入要修改的列号: " col
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    ! [[ "$col" =~ ^[0-9]+$ ]] || [[ $col -lt 1 ]] || [[ $col -gt $nf ]] && { echo -e "${RED}无效列号${NC}"; return; }
    local fn; fn=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    read -p "请输入新的 [$fn]: " new_val
    local new_line
    new_line=$(echo "$line" | awk -F',' -v c="$col" -v v="$new_val" 'BEGIN{OFS=","} {$c=v; print}')
    sed -i "s/^$sid,.*$/$new_line/" "$DATA_FILE"
    echo -e "${GREEN}修改成功！${NC}"
}

# ---------- 科目列表工具（带编号显示，i=6 跳过学号/姓名/e1/e2/e3） ----------
show_subject_menu() {
    local header; header=$(get_header)
    echo -e "${YELLOW}可选科目列表：${NC}"
    echo "$header" | awk -F',' '{for(i=6;i<=NF;i++) printf "%2d. %s\n", i-5, $i}'
}

# ========== 新增：为已有学生添加/修改某科成绩 ==========
add_subject_score() {
    echo -e "${CYAN}===== 为已有学生添加/修改某科成绩 =====${NC}"
    read -p "请输入学号: " sid
    local line; line=$(grep "^$sid," "$DATA_FILE" 2>/dev/null)
    [[ -z "$line" ]] && { echo -e "${RED}学号 $sid 不存在！${NC}"; return; }
    # 老师只能操作管辖班级
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        echo -e "${RED}权限不足！该学生不属于您管辖的班级。${NC}"; return
    fi
    # 显示学生当前信息
    local name; name=$(echo "$line" | awk -F',' '{print $2}')
    local cls; cls=$(get_student_class "$sid")
    echo -e "${YELLOW}当前学生：$name（$sid）班级：$cls${NC}"
    # 列出科目
    show_subject_menu
    read -p "请选择科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local header; header=$(get_header)
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    # 显示当前值
    local cur_val; cur_val=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
    [[ -n "$cur_val" ]] && echo -e "${YELLOW}当前 [$cname] = $cur_val${NC}" || echo -e "${YELLOW}当前 [$cname] =（空）${NC}"
    read -p "请输入新的成绩（回车取消）: " new_val
    [[ -z "$new_val" ]] && { echo -e "${YELLOW}已取消${NC}"; return; }
    # 用awk替换该列值
    local new_line
    new_line=$(echo "$line" | awk -F',' -v c="$col" -v v="$new_val" 'BEGIN{OFS=","} {$c=v; print}')
    sed -i "s/^$sid,.*$/$new_line/" "$DATA_FILE"
    echo -e "${GREEN}${name} 的「${cname}」成绩已设置为 $new_val${NC}"
}

# ========== 新增：批量录入某科成绩（最常用功能） ==========
batch_add_scores() {
    echo -e "${CYAN}===== 批量录入某科成绩 =====${NC}"
    echo -e "${YELLOW}适用场景：考完一场试，给全班登分${NC}\n"
    # 1. 选科目
    show_subject_menu
    read -p "请选择科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local header; header=$(get_header)
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')

    echo -e "\n${YELLOW}正在录入「${cname}」成绩${NC}"
    echo -e "每行输入「${GREEN}学号 成绩${NC}」（空格分隔），输入空行结束"
    echo -e "${YELLOW}提示：学号可输全10位或仅输后4位（自动补全 20181828）${NC}"
    echo ""

    # 2. 读取批量输入
    local batch_entries=()
    local has_error=0
    while true; do
        read -p "  > " input_line
        [[ -z "$input_line" ]] && break
        local input_sid input_score
        read -r input_sid input_score <<< "$input_line"
        [[ -z "$input_sid" || -z "$input_score" ]] && { echo -e "${RED}格式错误：需要「学号 成绩」${NC}"; ((has_error++)); continue; }
        # 短学号自动补全
        [[ ${#input_sid} -lt 10 ]] && input_sid="20181828${input_sid}"
        # 验证学号存在
        if ! grep -q "^$input_sid," "$DATA_FILE" 2>/dev/null; then
            echo -e "${RED}学号 $input_sid 不存在！已跳过${NC}"; ((has_error++)); continue
        fi
        # teacher 只能操作管辖班级
        if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$input_sid"; then
            local scls="${student_class[$input_sid]:-未知}"
            echo -e "${RED}权限不足！学号 $input_sid 属于 ${scls}，不在您管辖范围内${NC}"; ((has_error++)); continue
        fi
        batch_entries+=("$input_sid|$input_score")
    done

    local total=${#batch_entries[@]}
    [[ $total -eq 0 ]] && { echo -e "${YELLOW}未输入任何有效记录${NC}"; return; }

    # 3. 显示预览
    echo ""
    echo -e "${YELLOW}===== 录入预览（共 $total 条）=====${NC}"
    printf "%-16s %-8s %-10s %-10s\n" "学号" "姓名" "当前值" "新值"
    printf -- "----------------------------------------------\n"
    for entry in "${batch_entries[@]}"; do
        local sid score name cur
        sid="${entry%%|*}"
        score="${entry#*|}"
        name=$(grep "^$sid," "$DATA_FILE" | awk -F',' '{print $2}')
        cur=$(grep "^$sid," "$DATA_FILE" | awk -F',' -v c="$col" '{print $c}')
        printf "%-16s %-8s %-10s %-10s\n" "$sid" "$name" "${cur:-(空)}" "$score"
    done
    echo ""

    # 4. 确认写入
    read -p "确认录入以上 $total 条成绩？(y/n): " confirm
    [[ "$confirm" != [yY] ]] && { echo -e "${YELLOW}已取消${NC}"; return; }

    # 5. 逐条更新
    local success=0 fail=0
    for entry in "${batch_entries[@]}"; do
        local sid score line new_line
        sid="${entry%%|*}"
        score="${entry#*|}"
        line=$(grep "^$sid," "$DATA_FILE")
        new_line=$(echo "$line" | awk -F',' -v c="$col" -v v="$score" 'BEGIN{OFS=","} {$c=v; print}')
        if sed -i "s/^$sid,.*$/$new_line/" "$DATA_FILE" 2>/dev/null; then
            ((success++))
        else
            ((fail++))
        fi
    done

    echo -e "${GREEN}录入完成！成功 ${success} 条${NC}${fail:+, 失败 $fail 条${NC}}"
    echo -e "${YELLOW}科目：${cname}${NC}"
}

# ========== 新增：清除某科成绩 ==========
delete_subject_score() {
    echo -e "${CYAN}===== 清除某科成绩 =====${NC}"
    read -p "请输入学号: " sid
    local line; line=$(grep "^$sid," "$DATA_FILE" 2>/dev/null)
    [[ -z "$line" ]] && { echo -e "${RED}学号 $sid 不存在！${NC}"; return; }
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        echo -e "${RED}权限不足！该学生不属于您管辖的班级。${NC}"; return
    fi
    local name; name=$(echo "$line" | awk -F',' '{print $2}')
    echo -e "${YELLOW}学生：$name（$sid）${NC}"
    # 显示所有科目与当前成绩
    local header; header=$(get_header)
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    echo -e "\n${YELLOW}当前各科成绩：${NC}"
    for ((i=6; i<=nf; i++)); do
        local cname; cname=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
        local idx=$((i-5))
        printf "  %2d. %-28s %s\n" "$idx" "$cname" "${val:-(空)}"
    done
    read -p "请输入要清除的科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    local cur_val; cur_val=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
    [[ -z "$cur_val" ]] && { echo -e "${YELLOW}该科目已经为空，无需清除${NC}"; return; }
    echo -e "${RED}即将清除「$cname」= $cur_val${NC}"
    read -p "确认清除？(y/n): " confirm
    [[ "$confirm" != [yY] ]] && { echo -e "${YELLOW}已取消${NC}"; return; }
    local new_line
    new_line=$(echo "$line" | awk -F',' -v c="$col" 'BEGIN{OFS=","} {$c=""; print}')
    sed -i "s/^$sid,.*$/$new_line/" "$DATA_FILE"
    echo -e "${GREEN}已清除 ${name} 的「$cname」成绩${NC}"
}

# ========== 新增：按科目名选择修改（改进UI） ==========
modify_score_by_subject() {
    echo -e "${CYAN}===== 按科目修改成绩 =====${NC}"
    read -p "请输入学号: " sid
    local line; line=$(grep "^$sid," "$DATA_FILE" 2>/dev/null)
    [[ -z "$line" ]] && { echo -e "${RED}学号 $sid 不存在！${NC}"; return; }
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        echo -e "${RED}权限不足！该学生不属于您管辖的班级。${NC}"; return
    fi
    local name; name=$(echo "$line" | awk -F',' '{print $2}')
    local cls; cls=$(get_student_class "$sid")
    echo -e "${YELLOW}学生：$name（$sid）班级：$cls${NC}"
    # 显示各科成绩
    local header; header=$(get_header)
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    echo -e "\n${YELLOW}当前各科成绩：${NC}"
    for ((i=6; i<=nf; i++)); do
        local cname; cname=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
        printf "  %2d. %-28s %s\n" "$((i-5))" "$cname" "${val:-(空)}"
    done
    read -p "请选择要修改的科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    local cur_val; cur_val=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
    echo -e "${YELLOW}当前值: ${cur_val:-(空)}${NC}"
    read -p "请输入新的 [$cname]: " new_val
    [[ -z "$new_val" ]] && { echo -e "${YELLOW}已取消${NC}"; return; }
    local new_line
    new_line=$(echo "$line" | awk -F',' -v c="$col" -v v="$new_val" 'BEGIN{OFS=","} {$c=v; print}')
    sed -i "s/^$sid,.*$/$new_line/" "$DATA_FILE"
    echo -e "${GREEN}${name} 的「$cname」已由「${cur_val:-(空)}」改为「$new_val」${NC}"
}

# ========== 子菜单：添加记录 ==========
add_menu() {
    while true; do
        echo -e "\n${CYAN}===== 新增记录 =====${NC}"
        echo -e "  ${YELLOW}推荐：考完试给全班登分请用「批量录入」${NC}"
        echo "1. 批量录入某科成绩 ★ 推荐"
        echo "2. 录入单科成绩（单个学生）"
        echo "3. 添加新学生（完整记录）"
        echo "0. 返回主菜单"
        read -p "请选择: " aopt
        case $aopt in
            1) batch_add_scores ;;
            2) add_subject_score ;;
            3) add_student ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

# ========== 子菜单：删除记录 ==========
delete_menu() {
    while true; do
        echo -e "\n${CYAN}===== 删除记录 =====${NC}"
        echo "1. 删除学生（完整记录）"
        echo "2. 清除某科成绩"
        echo "0. 返回主菜单"
        read -p "请选择: " dopt
        case $dopt in
            1) delete_student ;;
            2) delete_subject_score ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

# ========== 子菜单：修改记录 ==========
modify_menu() {
    while true; do
        echo -e "\n${CYAN}===== 修改记录 =====${NC}"
        echo "1. 按列号修改（所有字段）"
        echo "2. 按科目名选择修改（更直观）"
        echo "0. 返回主菜单"
        read -p "请选择: " mopt
        case $mopt in
            1) modify_score ;;
            2) modify_score_by_subject ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

query_menu() {
    while true; do
        echo -e "\n${CYAN}===== 查询菜单 =====${NC}"
        echo "1. 某学生全部科目成绩（含总分/平均分）"
        echo "2. 模糊姓名查询"
        echo "3. 按科目成绩范围查询"
        echo "4. 某科 >= 指定分数的学生"
        echo "0. 返回"
        read -p "请选择: " qopt
        case $qopt in
            1) query_student_detail ;;
            2) query_by_name ;;
            3) query_by_score_range ;;
            4) query_by_subject_threshold ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

query_student_detail() {
    read -p "请输入学号: " sid
    # 学生只能查自己的成绩
    if [[ "$SESSION_ROLE" == "student" && "$sid" != "$SESSION_SCOPE" ]]; then
        echo -e "${RED}权限不足！学生只能查询自己的成绩。${NC}"
        return
    fi
    # 老师只能查管辖班级的学生
    if [[ "$SESSION_ROLE" == "teacher" ]] && ! teacher_can_manage_sid "$sid"; then
        echo -e "${RED}权限不足！该学生不属于您管辖的班级。${NC}"
        return
    fi
    local line; line=$(grep "^$sid," "$DATA_FILE" 2>/dev/null)
    [[ -z "$line" ]] && { echo -e "${RED}学号 $sid 不存在！${NC}"; return; }
    local header; header=$(get_header)
    local name; name=$(echo "$line" | awk -F',' '{print $2}')
    local cls; cls=$(get_student_class "$sid")
    echo -e "\n${CYAN}========== 学生：$name（$sid） 班级：$cls ==========${NC}"
    printf "%-30s %-10s %-8s\n" "科目" "成绩" "数值"
    printf "%-30s %-10s %-8s\n" "------------------------------" "----------" "--------"
    local total=0 count=0
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    for ((i=3; i<=nf; i++)); do
        local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        local raw_val; raw_val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
        local num_val; num_val=$(grade_to_num "$raw_val")
        if [[ -n "$raw_val" && "$raw_val" != "" ]]; then
            if [[ -n "$num_val" ]]; then
                printf "%-30s %-10s %-8s\n" "$course" "$raw_val" "$num_val"
                total=$(awk_add "$total" "$num_val")
                count=$((count + 1))
            else
                printf "%-30s %-10s %-8s\n" "$course" "$raw_val" "-"
            fi
        else
            printf "%-30s %-10s %-8s\n" "$course" "(空)" "-"
        fi
    done
    if [[ $count -gt 0 ]]; then
        local avg; avg=$(awk_div "$total" "$count")
        echo -e "\n${YELLOW}═══════════════════════════════════════${NC}"
        echo -e "有效科目数: $count"
        echo -e "总    分: ${GREEN}$total${NC}"
        echo -e "平 均 分: ${GREEN}$avg${NC}"
    fi
}

query_by_name() {
    read -p "请输入姓名关键字: " keyword
    echo -e "\n${CYAN}===== 姓名模糊匹配结果 =====${NC}"
    printf "%-14s %-8s %-12s\n" "学号" "姓名" "班级"
    printf -- "----------------------------------\n"
    while IFS= read -r line; do
        local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
        local sname; sname=$(echo "$line" | awk -F',' '{print $2}')
        if echo "$sname" | grep -q "$keyword"; then
            local cls; cls=$(get_student_class "$sid")
            printf "%-14s %-8s %-12s\n" "$sid" "$sname" "$cls"
        fi
    done < <(get_data_lines)
    local cnt; cnt=$(get_data_lines | awk -F',' -v k="$keyword" '$2 ~ k {c++} END{print c+0}')
    echo -e "\n${GREEN}共找到 $cnt 条记录${NC}"
}

query_by_score_range() {
    echo -e "\n${YELLOW}可选科目列表：${NC}"
    local header; header=$(get_header)
    echo "$header" | awk -F',' '{for(i=6;i<=NF;i++) printf "%2d. %s\n", i-5, $i}'
    read -p "请选择科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    read -p "最低分: " min_score
    read -p "最高分（回车不限制）: " max_score
    [[ -z "$max_score" ]] && max_score=100
    echo -e "\n${CYAN}===== $cname 成绩在 $min_score ~ $max_score 的学生 =====${NC}"
    printf "%-14s %-8s %-12s %-10s\n" "学号" "姓名" "班级" "成绩"
    printf -- "--------------------------------------------\n"
    local count=0
    while IFS= read -r line; do
        local sid sname raw_val num_val
        sid=$(echo "$line" | awk -F',' '{print $1}')
        sname=$(echo "$line" | awk -F',' '{print $2}')
        raw_val=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
        num_val=$(grade_to_num "$raw_val")
        if [[ -n "$num_val" ]]; then
            local ge1 le2
            ge1=$(awk_ge "$num_val" "$min_score")
            le2=$(awk_ge "$max_score" "$num_val")
            if [[ "$ge1" == "1" && "$le2" == "1" ]]; then
                local cls; cls=$(get_student_class "$sid")
                printf "%-14s %-8s %-12s %-10s\n" "$sid" "$sname" "$cls" "$raw_val"
                count=$((count + 1))
            fi
        fi
    done < <(get_data_lines)
    echo -e "\n${GREEN}共 $count 人${NC}"
}

query_by_subject_threshold() {
    echo -e "\n${YELLOW}可选科目列表：${NC}"
    local header; header=$(get_header)
    echo "$header" | awk -F',' '{for(i=6;i<=NF;i++) printf "%2d. %s\n", i-5, $i}'
    read -p "请选择科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    read -p "阈值（>=）: " threshold
    echo -e "\n${CYAN}===== $cname >= $threshold 分的学生 =====${NC}"
    printf "%-14s %-8s %-12s %-10s\n" "学号" "姓名" "班级" "成绩"
    printf -- "--------------------------------------------\n"
    local count=0
    while IFS= read -r line; do
        local sid sname raw_val num_val
        sid=$(echo "$line" | awk -F',' '{print $1}')
        sname=$(echo "$line" | awk -F',' '{print $2}')
        raw_val=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
        num_val=$(grade_to_num "$raw_val")
        if [[ -n "$num_val" ]]; then
            local ge; ge=$(awk_ge "$num_val" "$threshold")
            if [[ "$ge" == "1" ]]; then
                local cls; cls=$(get_student_class "$sid")
                printf "%-14s %-8s %-12s %-10s\n" "$sid" "$sname" "$cls" "$raw_val"
                count=$((count + 1))
            fi
        fi
    done < <(get_data_lines)
    echo -e "\n${GREEN}共 $count 人${NC}"
}

# ========== 排序 ==========
sort_menu() {
    while true; do
        echo -e "\n${CYAN}===== 排序菜单 =====${NC}"
        echo "1. 按某科成绩排序"
        echo "2. 按总分排序"
        echo "3. 按平均分排序"
        echo "0. 返回"
        read -p "请选择: " sopt
        case $sopt in
            1) sort_by_subject ;;
            2) sort_by_total ;;
            3) sort_by_average ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

sort_by_subject() {
    echo -e "\n${YELLOW}可选科目列表：${NC}"
    local header; header=$(get_header)
    echo "$header" | awk -F',' '{for(i=6;i<=NF;i++) printf "%2d. %s\n", i-5, $i}'
    read -p "请选择科目编号 (1-27): " cid
    ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
    local col=$((cid + 5))
    local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
    read -p "排序方式: 1=升序  2=降序: " order
    echo -e "\n${CYAN}===== 按《$cname》成绩排序 =====${NC}"
    printf "%-14s %-8s %-12s %-10s\n" "学号" "姓名" "班级" "成绩"
    printf -- "--------------------------------------------\n"
    get_data_lines | awk -F',' -v c="$col" '
    '"$(get_toNum_awk)"'
    { num = toNum($c); printf "%f\t%s\t%s\n", num, $1, $2 }' | sort -t$'\t' -k1 $([ "$order" == "2" ] && echo "-rn" || echo "-n") | while IFS=$'\t' read -r _ sid sname; do
        local raw; raw=$(grep "^$sid," "$DATA_FILE" | awk -F',' -v c="$col" '{print $c}')
        local cls; cls=$(get_student_class "$sid")
        printf "%-14s %-8s %-12s %-10s\n" "$sid" "$sname" "$cls" "$raw"
    done
}

sort_by_total() {
    read -p "排序方式: 1=升序  2=降序: " order
    echo -e "\n${CYAN}===== 按总分排序 =====${NC}"
    printf "%-14s %-8s %-12s %-8s %-8s\n" "学号" "姓名" "班级" "总分" "有效科数"
    printf -- "------------------------------------------------\n"
    get_data_lines | awk -F',' '
    '"$(get_toNum_awk)"'
    { total = 0; count = 0
        for (i=3; i<=NF; i++) { n = toNum($i); if (n >= 0) { total += n; count++ } }
        printf "%.2f|%s|%s|%d\n", total, $1, $2, count
    }' | sort -t'|' -k1 $([ "$order" == "2" ] && echo "-rn" || echo "-n") | while IFS='|' read -r total sid sname cnt; do
        local cls; cls=$(get_student_class "$sid")
        printf "%-14s %-8s %-12s %-8s %-8s\n" "$sid" "$sname" "$cls" "$total" "$cnt"
    done
}

sort_by_average() {
    read -p "排序方式: 1=升序  2=降序: " order
    echo -e "\n${CYAN}===== 按平均分排序 =====${NC}"
    printf "%-14s %-8s %-12s %-8s %-8s\n" "学号" "姓名" "班级" "平均分" "有效科数"
    printf -- "------------------------------------------------\n"
    get_data_lines | awk -F',' '
    '"$(get_toNum_awk)"'
    { total = 0; count = 0
        for (i=3; i<=NF; i++) { n = toNum($i); if (n >= 0) { total += n; count++ } }
        if (count > 0) { avg = total / count; printf "%.2f|%s|%s|%d\n", avg, $1, $2, count }
    }' | sort -t'|' -k1 $([ "$order" == "2" ] && echo "-rn" || echo "-n") | while IFS='|' read -r avg sid sname cnt; do
        local cls; cls=$(get_student_class "$sid")
        printf "%-14s %-8s %-12s %-8s %-8s\n" "$sid" "$sname" "$cls" "$avg" "$cnt"
    done
}

# =============================================================
#  ★★★  加分功能：学院/班级维度 + 三级权限 + 报表导出
# =============================================================

statistics_menu() {
    while true; do
        echo -e "\n${CYAN}========================================${NC}"
        echo -e "${YELLOW}   ★★★ 加分模块：学院/班级统计与权限${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo ""
        echo "  ┌── 统计报表 ─────────────────┐"
        echo "  │ 1. 各科成绩分布（优/良/中/及格/不及格）│"
        echo "  │ 2. 各科平均分/最高/最低              │"
        echo "  │ 3. 加权学分绩点（GPA）排名          │"
        echo "  │ 4. 挂科（不及格）名单               │"
        echo "  │ 5. 全体学生成绩总览                 │"
        echo "  ├── ★ 学院/班级维度 ────────┤"
        echo "  │ 6. 按班级统计成绩（平均分/通过率）   │"
        echo "  │ 7. 按学院/系汇总统计                │"
        echo "  │ 8. 班级成绩排名                     │"
        echo "  ├── ★ 用户与权限 ───────────┤"
        echo "  │ 9.  管理用户（Admin only）          │"
        echo "  ├── ★ 报表导出 ────────────┤"
        echo "  │ 10. 导出全部统计报表到 report/      │"
        echo "  └──────────────────────────────┘"
        echo "  0. 返回主菜单"
        echo ""
        read -p "请选择 [0-10]: " statopt
        case $statopt in
            1) subject_distribution ;;
            2) subject_stats ;;
            3) weighted_gpa_ranking ;;
            4) fail_list ;;
            5) all_student_summary ;;
            6) class_stats ;;
            7) college_dept_stats ;;
            8) class_ranking ;;
            9) user_management ;;
            10) export_all_reports ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

# --- 原有统计函数（增强学院班级信息） ---

subject_distribution() {
    echo -e "\n${CYAN}===== 各科成绩分布统计 =====${NC}"
    local header; header=$(get_header)
    printf "%-30s %-8s %-8s %-8s %-8s %-8s\n" "科目" "优秀" "良好" "中等" "及格" "不及格"
    printf -- "------------------------------------------------------------------------\n"
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    for ((i=6; i<=nf; i++)); do
        local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        local you=0 liang=0 zhong=0 jige=0 bujige=0
        while IFS= read -r line; do
            local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
            local num; num=$(grade_to_num "$val")
            if [[ -n "$num" ]]; then
                if [[ "$(awk_ge "$num" "90")" == "1" ]]; then ((you++))
                elif [[ "$(awk_ge "$num" "80")" == "1" ]]; then ((liang++))
                elif [[ "$(awk_ge "$num" "70")" == "1" ]]; then ((zhong++))
                elif [[ "$(awk_ge "$num" "60")" == "1" ]]; then ((jige++))
                else ((bujige++))
                fi
            fi
        done < <(get_data_lines)
        printf "%-30s %-8s %-8s %-8s %-8s %-8s\n" "${course:0:28}" "$you" "$liang" "$zhong" "$jige" "$bujige"
    done
}

subject_stats() {
    echo -e "\n${CYAN}===== 各科平均分/最高/最低 =====${NC}"
    local header; header=$(get_header)
    printf "%-30s %-8s %-8s %-8s %-8s\n" "科目" "平均分" "最高" "最低" "人数"
    printf -- "------------------------------------------------------------------------\n"
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    for ((i=3; i<=nf; i++)); do
        local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        local sum=0 cnt=0 min=100 max=0
        while IFS= read -r line; do
            local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
            local num; num=$(grade_to_num "$val")
            if [[ -n "$num" ]]; then
                sum=$(awk_add "$sum" "$num"); cnt=$((cnt + 1))
                [[ "$(awk_lt "$num" "$min")" == "1" ]] && min=$num
                [[ "$(awk_gt "$num" "$max")" == "1" ]] && max=$num
            fi
        done < <(get_data_lines)
        if [[ $cnt -gt 0 ]]; then
            local avg; avg=$(awk_div "$sum" "$cnt")
            printf "%-30s %-8s %-8s %-8s %-8s\n" "${course:0:28}" "$avg" "$max" "$min" "$cnt"
        fi
    done
}

weighted_gpa_ranking() {
    echo -e "\n${CYAN}===== ★ 加权学分绩点（GPA）排名 =====${NC}"
    echo -e "${YELLOW}GPA = Σ(课程成绩 × 学分) / Σ 总学分${NC}\n"
    local header; header=$(get_header)
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    local credits=()
    for ((i=6; i<=nf; i++)); do
        local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
        local cr; cr=$(extract_credit "$course"); [[ -z "$cr" ]] && cr=0
        credits[$i]=$cr
    done
    printf "%-14s %-8s %-12s %-10s %-8s\n" "学号" "姓名" "班级" "加权GPA" "有效学分"
    printf -- "------------------------------------------------\n"
    local tmpfile; tmpfile=$(mktemp)
    while IFS= read -r line; do
        local sid sname
        sid=$(echo "$line" | awk -F',' '{print $1}')
        sname=$(echo "$line" | awk -F',' '{print $2}')
        local ws=0 tc=0
        for ((i=6; i<=nf; i++)); do
            local cr=${credits[$i]}; [[ -z "$cr" || "$cr" == "0" ]] && continue
            local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
            local num; num=$(grade_to_num "$val")
            if [[ -n "$num" ]]; then
                ws=$(awk_add "$ws" "$(awk_mul "$num" "$cr")")
                tc=$(awk_add "$tc" "$cr")
            fi
        done
        if [[ "$(awk_gt "$tc" "0")" == "1" ]]; then
            local gpa; gpa=$(awk_div "$ws" "$tc")
            echo "$gpa|$sid|$sname|$tc" >> "$tmpfile"
        fi
    done < <(get_data_lines)
    sort -t'|' -k1 -rn "$tmpfile" | while IFS='|' read -r gpa sid sname tc; do
        local cls; cls=$(get_student_class "$sid")
        printf "%-14s %-8s %-12s %-10s %-8s\n" "$sid" "$sname" "$cls" "$gpa" "$tc"
    done
    rm -f "$tmpfile"
}

fail_list() {
    echo -e "\n${CYAN}===== 挂科（不及格）名单 =====${NC}"
    local header; header=$(get_header)
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
    printf "%-14s %-8s %-12s %-30s %-10s\n" "学号" "姓名" "班级" "挂科科目" "成绩"
    printf -- "------------------------------------------------------------------------\n"
    local total_fail=0
    while IFS= read -r line; do
        local sid sname
        sid=$(echo "$line" | awk -F',' '{print $1}')
        sname=$(echo "$line" | awk -F',' '{print $2}')
        local cls; cls=$(get_student_class "$sid")
        for ((i=6; i<=nf; i++)); do
            local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
            local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
            local num; num=$(grade_to_num "$val")
            if [[ -n "$num" ]] && [[ "$(awk_lt "$num" "60")" == "1" ]]; then
                printf "%-14s %-8s %-12s %-30s %-10s\n" "$sid" "$sname" "$cls" "$course" "$val"
                total_fail=$((total_fail + 1))
            fi
        done
    done < <(get_data_lines)
    echo -e "\n${RED}共有 $total_fail 科次不及格${NC}"
}

all_student_summary() {
    echo -e "\n${CYAN}===== 全体学生成绩总览 =====${NC}"
    printf "%-14s %-8s %-12s %-8s %-8s %-8s\n" "学号" "姓名" "班级" "总分" "平均分" "有效科数"
    printf -- "--------------------------------------------------------\n"
    get_data_lines | while IFS= read -r line; do
        local sid sname
        sid=$(echo "$line" | awk -F',' '{print $1}')
        sname=$(echo "$line" | awk -F',' '{print $2}')
        local cls; cls=$(get_student_class "$sid")
        local stats; stats=$(calc_stats_for_line "$line")
        IFS='|' read -r total cnt avg <<< "$stats"
        printf "%-14s %-8s %-12s %-8s %-8s %-8s\n" "$sid" "$sname" "$cls" "$total" "$avg" "$cnt"
    done
}

# ========== ★ 新增：按班级统计 ==========
class_stats() {
    echo -e "\n${CYAN}===== ★ 按班级统计成绩 =====${NC}"
    printf "%-14s %-12s %-10s %-10s %-8s %-8s\n" "班级" "所属学院" "人数" "平均分" "最高均分" "及格率"
    printf -- "------------------------------------------------------------------------\n"

    # 收集所有班级
    local classes class_list=()
    for cls in "${!class_college[@]}"; do
        class_list+=("$cls")
    done

    for cls in "${class_list[@]}"; do
        local clg="${class_college[$cls]}"
        local students=()
        # 找该班级的学生
        while IFS= read -r line; do
            local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
            [[ "$sid" == "学号" || -z "$sid" ]] && continue
            local scls; scls=$(get_student_class "$sid")
            if [[ "$scls" == "$cls" ]]; then
                students+=("$line")
            fi
        done < <(get_data_lines)

        local n=${#students[@]}
        [[ $n -eq 0 ]] && continue

        local sum_avg=0 pass_count=0
        for sline in "${students[@]}"; do
            local stats; stats=$(calc_stats_for_line "$sline")
            IFS='|' read -r total cnt avg <<< "$stats"
            sum_avg=$(awk_add "$sum_avg" "$avg")
            if [[ "$(awk_ge "$avg" "60")" == "1" ]]; then
                pass_count=$((pass_count + 1))
            fi
        done
        local class_avg; class_avg=$(awk_div "$sum_avg" "$n")
        local pass_rate; pass_rate=$(awk_div "$(awk_mul "$pass_count" "100")" "$n")

        # 找到该班级中最高平均分的学生
        local max_avg=0
        for sline in "${students[@]}"; do
            local stats2; stats2=$(calc_stats_for_line "$sline")
            IFS='|' read -r _ _ avg2 <<< "$stats2"
            if [[ "$(awk_gt "$avg2" "$max_avg")" == "1" ]]; then
                max_avg=$avg2
            fi
        done

        printf "%-14s %-12s %-10s %-10s %-8s %-8s%%\n" "$cls" "$clg" "$n" "$class_avg" "$max_avg" "$pass_rate"
    done
}

# ========== ★ 新增：按学院/系汇总 ==========
college_dept_stats() {
    echo -e "\n${CYAN}===== ★ 学院/系级汇总统计 =====${NC}"

    # 按学院汇总
    echo -e "\n${YELLOW}【按学院汇总】${NC}"
    printf "%-24s %-8s %-10s %-10s\n" "学院" "班级数" "学生数" "平均分"
    printf -- "------------------------------------------------\n"
    declare -A clg_classes clg_students clg_score_sum

    # 使用 get_data_lines 实现数据隔离
    while IFS= read -r line; do
        local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
        [[ -z "$sid" || "$sid" == "学号" ]] && continue
        local cls="${student_class[$sid]:-未知}"
        local clg="${class_college[$cls]:-未知学院}"
        clg_classes["$clg"]="${clg_classes[$clg]} $cls"
        clg_students["$clg"]=$((clg_students["$clg"] + 1))
        local stats; stats=$(calc_stats_for_line "$line")
        IFS='|' read -r _ _ avg <<< "$stats"
        clg_score_sum["$clg"]=$(awk_add "${clg_score_sum[$clg]:-0}" "$avg")
    done < <(get_data_lines)

    for clg in "${!clg_students[@]}"; do
        local n_classes; n_classes=$(echo "${clg_classes[$clg]}" | tr ' ' '\n' | sort -u | grep -c .)
        local n_stu=${clg_students[$clg]}
        local avg; avg=$(awk_div "${clg_score_sum[$clg]}" "$n_stu")
        printf "%-24s %-8s %-10s %-10s\n" "$clg" "$n_classes" "$n_stu" "$avg"
    done

    # 按系汇总
    echo -e "\n${YELLOW}【按系汇总】${NC}"
    printf "%-24s %-8s %-10s\n" "系" "学生数" "平均分"
    printf -- "--------------------------------------------\n"
    declare -A dept_students dept_sum
    while IFS= read -r line; do
        local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
        [[ -z "$sid" || "$sid" == "学号" ]] && continue
        local cls="${student_class[$sid]:-未知}"
        local dept="${class_dept[$cls]:-未知系}"
        dept_students["$dept"]=$((dept_students["$dept"] + 1))
        local stats; stats=$(calc_stats_for_line "$line")
        IFS='|' read -r _ _ avg <<< "$stats"
        dept_sum["$dept"]=$(awk_add "${dept_sum[$dept]:-0}" "$avg")
    done < <(get_data_lines)
    for dept in "${!dept_students[@]}"; do
        local n=${dept_students[$dept]}
        local avg; avg=$(awk_div "${dept_sum[$dept]}" "$n")
        printf "%-24s %-8s %-10s\n" "$dept" "$n" "$avg"
    done
}

# ========== ★ 新增：班级成绩排名 ==========
class_ranking() {
    echo -e "\n${CYAN}===== ★ 班级成绩排名 =====${NC}"
    local header; header=$(get_header)
    local nf; nf=$(echo "$header" | awk -F',' '{print NF}')

    # 选一个科目作为比较
    echo -e "${YELLOW}请选择比较维度：${NC}"
    echo "1. 按班级总分平均排名"
    echo "2. 按指定科目班级均分排名"
    read -p "请选择: " rank_dim

    if [[ "$rank_dim" == "2" ]]; then
        echo "$header" | awk -F',' '{for(i=6;i<=NF;i++) printf "%2d. %s\n", i-5, $i}'
        read -p "请选择科目编号 (1-27): " cid
        ! [[ "$cid" =~ ^[0-9]+$ ]] || [[ $cid -lt 1 ]] || [[ $cid -gt 27 ]] && { echo -e "${RED}无效编号${NC}"; return; }
        local col=$((cid + 5))
        local cname; cname=$(echo "$header" | awk -F',' -v idx="$col" '{print $idx}')
        echo -e "\n${CYAN}按《$cname》班级均分排名：${NC}"

        printf "%-14s %-12s %-10s %-10s\n" "排名" "班级" "人数" "科目均分"
        printf -- "--------------------------------------------\n"

        local tmpf; tmpf=$(mktemp)
        declare -A cls_list
        for cls in "${!class_college[@]}"; do cls_list["$cls"]=1; done

        for cls in "${!cls_list[@]}"; do
            local sum=0 cnt=0
            while IFS= read -r line; do
                local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
                [[ "$sid" == "学号" ]] && continue
                local scls; scls=$(get_student_class "$sid")
                if [[ "$scls" == "$cls" ]]; then
                    local val; val=$(echo "$line" | awk -F',' -v c="$col" '{if(c<=NF) print $c}')
                    local num; num=$(grade_to_num "$val")
                    if [[ -n "$num" ]]; then
                        sum=$(awk_add "$sum" "$num")
                        cnt=$((cnt + 1))
                    fi
                fi
            done < <(get_data_lines)
            if [[ $cnt -gt 0 ]]; then
                local avg; avg=$(awk_div "$sum" "$cnt")
                echo "$avg|$cls|$cnt" >> "$tmpf"
            fi
        done
        sort -t'|' -k1 -rn "$tmpf" | cat -n | while IFS=$'\t' read -r rank line; do
            rank=$(echo "$rank" | xargs)
            IFS='|' read -r avg cls cnt <<< "$line"
            printf "第%-2s名    %-12s %-10s %-10s\n" "$rank" "$cls" "$cnt" "$avg"
        done
        rm -f "$tmpf"
    else
        # 按班级总分平均排名
        printf "%-14s %-12s %-10s %-10s %-8s\n" "排名" "班级" "人数" "总分均分" "平均GPA"
        printf -- "------------------------------------------------\n"
        local tmpf2; tmpf2=$(mktemp)
        declare -A cls_list2
        for cls in "${!class_college[@]}"; do cls_list2["$cls"]=1; done
        for cls in "${!cls_list2[@]}"; do
            local sum=0 cnt=0
            while IFS= read -r line; do
                local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
                [[ "$sid" == "学号" ]] && continue
                local scls; scls=$(get_student_class "$sid")
                if [[ "$scls" == "$cls" ]]; then
                    local stats; stats=$(calc_stats_for_line "$line")
                    IFS='|' read -r total _ avg <<< "$stats"
                    sum=$(awk_add "$sum" "$avg")
                    cnt=$((cnt + 1))
                fi
            done < <(get_data_lines)
            if [[ $cnt -gt 0 ]]; then
                local class_avg; class_avg=$(awk_div "$sum" "$cnt")
                echo "$class_avg|$cls|$cnt" >> "$tmpf2"
            fi
        done
        sort -t'|' -k1 -rn "$tmpf2" | cat -n | while IFS=$'\t' read -r rank line; do
            rank=$(echo "$rank" | xargs)
            IFS='|' read -r avg cls cnt <<< "$line"
            printf "第%-2s名    %-12s %-10s %-10s %-8s\n" "$rank" "$cls" "$cnt" "$avg" "$avg"
        done
        rm -f "$tmpf2"
    fi
}

# ========== ★ 新增：用户管理（仅 Admin） ==========
user_management() {
    if [[ "$SESSION_ROLE" != "admin" ]]; then
        echo -e "${RED}权限不足！仅 admin 角色可管理用户。${NC}"
        return
    fi
    while true; do
        echo -e "\n${CYAN}===== ★ 用户管理（Admin Only） =====${NC}"
        echo "1. 列出所有用户"
        echo "2. 添加用户"
        echo "3. 删除用户"
        echo "0. 返回"
        read -p "请选择: " uopt
        case $uopt in
            1)
                echo -e "\n${YELLOW}当前用户列表：${NC}"
                printf "%-15s %-10s\n" "用户名" "角色"
                printf -- "------------------------\n"
                grep -v '^#' "$USER_FILE" | awk -F'|' '{printf "%-15s %-10s\n", $1, $3}'
                ;;
            2)
                read -p "新用户名: " newu
                read -s -p "密码: " newp; echo ""
                read -p "角色 (admin/teacher/student): " newr
                if [[ "$newr" != "admin" && "$newr" != "teacher" && "$newr" != "student" ]]; then
                    echo -e "${RED}无效角色！${NC}"; continue
                fi
                echo "$newu|$newp|$newr" >> "$USER_FILE"
                echo -e "${GREEN}用户 $newu 创建成功!${NC}"
                ;;
            3)
                read -p "要删除的用户名: " delu
                [[ "$delu" == "admin" ]] && { echo -e "${RED}不能删除超级管理员${NC}"; continue; }
                sed -i "/^$delu|/d" "$USER_FILE" && echo -e "${GREEN}已删除${NC}"
                ;;
            0) break ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

# ========== ★ 新增：导出全部报表到 report/ ==========
export_all_reports() {
    echo -e "\n${CYAN}===== ★ 导出报表到 $REPORT_DIR =====${NC}"
    mkdir -p "$REPORT_DIR"

    local ts; ts=$(date '+%Y%m%d_%H%M%S')
    local base="$REPORT_DIR/report_$ts"

    # 1. 全体成绩总览
    local f1="${base}_全体总览.txt"
    {
        echo "============================================"
        echo "  全体学生成绩总览（导出时间: $(date)）"
        echo "============================================"
        printf "%-14s %-8s %-12s %-8s %-8s %-8s\n" "学号" "姓名" "班级" "总分" "平均分" "有效科数"
        printf -- "--------------------------------------------------------\n"
        get_data_lines | while IFS= read -r line; do
            local sid sname
            sid=$(echo "$line" | awk -F',' '{print $1}')
            sname=$(echo "$line" | awk -F',' '{print $2}')
            local cls; cls=$(get_student_class "$sid")
            local stats; stats=$(calc_stats_for_line "$line")
            IFS='|' read -r total cnt avg <<< "$stats"
            printf "%-14s %-8s %-12s %-8s %-8s %-8s\n" "$sid" "$sname" "$cls" "$total" "$avg" "$cnt"
        done
    } > "$f1"
    echo -e "  ${GREEN}✓${NC} 全体总览: $f1"

    # 2. 班级统计
    local f2="${base}_班级统计.txt"
    {
        echo "============================================"
        echo "  班级统计报表"
        echo "============================================"
        printf "%-14s %-12s %-10s %-10s %-8s %-8s\n" "班级" "所属学院" "人数" "平均分" "最高均分" "及格率"
        printf -- "------------------------------------------------------------------------\n"
        declare -A cls_set
        for cls in "${!class_college[@]}"; do cls_set["$cls"]=1; done
        for cls in "${!cls_set[@]}"; do
            local clg="${class_college[$cls]}"
            local students=()
            while IFS= read -r line; do
                local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
                [[ "$sid" == "学号" || -z "$sid" ]] && continue
                [[ "$(get_student_class "$sid")" == "$cls" ]] && students+=("$line")
            done < <(get_data_lines)
            local n=${#students[@]}; [[ $n -eq 0 ]] && continue
            local sum_avg=0 pass_count=0 max_avg=0
            for sline in "${students[@]}"; do
                local stats; stats=$(calc_stats_for_line "$sline")
                IFS='|' read -r _ _ avg <<< "$stats"
                sum_avg=$(awk_add "$sum_avg" "$avg")
                [[ "$(awk_ge "$avg" "60")" == "1" ]] && pass_count=$((pass_count + 1))
                [[ "$(awk_gt "$avg" "$max_avg")" == "1" ]] && max_avg=$avg
            done
            local class_avg; class_avg=$(awk_div "$sum_avg" "$n")
            local pass_rate; pass_rate=$(awk_div "$(awk_mul "$pass_count" "100")" "$n")
            printf "%-14s %-12s %-10s %-10s %-8s %-8s%%\n" "$cls" "$clg" "$n" "$class_avg" "$max_avg" "$pass_rate"
        done
    } > "$f2"
    echo -e "  ${GREEN}✓${NC} 班级统计: $f2"

    # 3. GPA 排名
    local f3="${base}_GPA排名.txt"
    {
        echo "============================================"
        echo "  加权 GPA 排名"
        echo "============================================"
        local header; header=$(get_header)
        local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
        local credits=()
        for ((i=6; i<=nf; i++)); do
            local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
            local cr; cr=$(extract_credit "$course"); [[ -z "$cr" ]] && cr=0
            credits[$i]=$cr
        done
        printf "%-14s %-8s %-12s %-10s %-8s\n" "排名" "姓名" "班级" "加权GPA" "有效学分"
        printf -- "------------------------------------------------\n"
        local tmpf; tmpf=$(mktemp)
        while IFS= read -r line; do
            local sid sname
            sid=$(echo "$line" | awk -F',' '{print $1}')
            sname=$(echo "$line" | awk -F',' '{print $2}')
            local ws=0 tc=0
            for ((i=6; i<=nf; i++)); do
                local cr=${credits[$i]}; [[ -z "$cr" || "$cr" == "0" ]] && continue
                local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
                local num; num=$(grade_to_num "$val")
                if [[ -n "$num" ]]; then
                    ws=$(awk_add "$ws" "$(awk_mul "$num" "$cr")")
                    tc=$(awk_add "$tc" "$cr")
                fi
            done
            [[ "$(awk_gt "$tc" "0")" == "1" ]] && {
                local gpa; gpa=$(awk_div "$ws" "$tc")
                echo "$gpa|$sid|$sname|$tc" >> "$tmpf"
            }
        done < <(get_data_lines)
        sort -t'|' -k1 -rn "$tmpf" | cat -n | while IFS=$'\t' read -r rank line; do
            rank=$(echo "$rank" | xargs)
            IFS='|' read -r gpa sid sname tc <<< "$line"
            local cls; cls=$(get_student_class "$sid")
            printf "第%-2s名    %-8s %-12s %-10s %-8s\n" "$rank" "$sname" "$cls" "$gpa" "$tc"
        done
        rm -f "$tmpf"
    } > "$f3"
    echo -e "  ${GREEN}✓${NC} GPA排名: $f3"

    # 4. 挂科名单
    local f4="${base}_挂科名单.txt"
    {
        echo "============================================"
        echo "  挂科（不及格）名单"
        echo "============================================"
        local header; header=$(get_header)
        local nf; nf=$(echo "$header" | awk -F',' '{print NF}')
        printf "%-14s %-8s %-12s %-30s %-10s\n" "学号" "姓名" "班级" "挂科科目" "成绩"
        printf -- "------------------------------------------------------------------------\n"
        local total_fail=0
        while IFS= read -r line; do
            local sid sname
            sid=$(echo "$line" | awk -F',' '{print $1}')
            sname=$(echo "$line" | awk -F',' '{print $2}')
            local cls; cls=$(get_student_class "$sid")
            for ((i=6; i<=nf; i++)); do
                local course; course=$(echo "$header" | awk -F',' -v idx="$i" '{print $idx}')
                local val; val=$(echo "$line" | awk -F',' -v c="$i" '{if(c<=NF) print $c}')
                local num; num=$(grade_to_num "$val")
                if [[ -n "$num" ]] && [[ "$(awk_lt "$num" "60")" == "1" ]]; then
                    printf "%-14s %-8s %-12s %-30s %-10s\n" "$sid" "$sname" "$cls" "$course" "$val"
                    total_fail=$((total_fail + 1))
                fi
            done
        done < <(get_data_lines)
        echo ""
        echo "共有 $total_fail 科次不及格"
    } > "$f4"
    echo -e "  ${GREEN}✓${NC} 挂科名单: $f4"

    # 5. 学院统计
    local f5="${base}_学院统计.txt"
    {
        echo "============================================"
        echo "  学院级汇总统计"
        echo "============================================"
        echo ""
        echo "【按学院汇总】"
        printf "%-24s %-8s %-10s %-10s\n" "学院" "班级数" "学生数" "平均分"
        printf -- "------------------------------------------------\n"
        declare -A clg_c clg_s clg_ss
        while IFS= read -r line; do
            local sid; sid=$(echo "$line" | awk -F',' '{print $1}')
            [[ -z "$sid" || "$sid" == "学号" ]] && continue
            local cls="${student_class[$sid]:-未知}"
            local clg="${class_college[$cls]:-未知学院}"
            clg_c["$clg"]="${clg_c[$clg]} $cls"
            clg_s["$clg"]=$((clg_s["$clg"] + 1))
            local stats; stats=$(calc_stats_for_line "$line")
            IFS='|' read -r _ _ avg <<< "$stats"
            clg_ss["$clg"]=$(awk_add "${clg_ss[$clg]:-0}" "$avg")
        done < <(get_data_lines)
        for clg in "${!clg_s[@]}"; do
            local nc; nc=$(echo "${clg_c[$clg]}" | tr ' ' '\n' | sort -u | grep -c .)
            local ns=${clg_s[$clg]}
            local avg; avg=$(awk_div "${clg_ss[$clg]}" "$ns")
            printf "%-24s %-8s %-10s %-10s\n" "$clg" "$nc" "$ns" "$avg"
        done
    } > "$f5"
    echo -e "  ${GREEN}✓${NC} 学院统计: $f5"

    echo ""
    echo -e "${GREEN}全部报表已导出到: $REPORT_DIR/${NC}"
    ls -lh "$REPORT_DIR/" | grep "$ts"
}

# =============================================================
#  主菜单（角色相关）
# =============================================================
main_menu() {
    while true; do
        echo ""
        echo -e "${CYAN}========================================${NC}"
        echo -e "${GREEN}     Linux 作业五 — 成绩管理系统${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo -e "  当前用户: ${BLUE}$SESSION_USER${NC}  (${YELLOW}$SESSION_ROLE${NC})"
        echo ""
        echo "  1. 新增记录（批量录入 / 单科 / 新学生）"
        echo "  2. 删除记录（删学生 / 清某科）"
        echo "  3. 修改记录（按列号 / 按科目名）"
        echo "  4. 查询成绩信息"
        echo "  5. 排序显示"
        echo "  ----------"
        echo -e "  ${YELLOW}6. ★ 加分模块：学院/班级/权限/报表${NC}"
        echo "  ----------"
        echo "  0. 退出"
        echo ""

        # 角色权限控制
        local menu_items="1-6"
        if [[ "$SESSION_ROLE" == "student" ]]; then
            menu_items="4,5,6"  # 学生只能查询和查看统计
        elif [[ "$SESSION_ROLE" == "teacher" ]]; then
            menu_items="1-6"    # 教师可增删改查
        fi

        read -p "请输入选项 [0-6]: " opt
        case $opt in
            1)
                if [[ "$SESSION_ROLE" == "student" ]]; then echo -e "${RED}学生无此权限${NC}"; else add_menu; fi ;;
            2)
                if [[ "$SESSION_ROLE" == "student" ]]; then echo -e "${RED}学生无此权限${NC}"; else delete_menu; fi ;;
            3)
                if [[ "$SESSION_ROLE" == "student" ]]; then echo -e "${RED}学生无此权限${NC}"; else modify_menu; fi ;;
            4) query_menu ;;
            5) sort_menu ;;
            6) statistics_menu ;;
            0) echo -e "${GREEN}感谢使用！${NC}"; exit 0 ;;
            *) echo -e "${RED}无效选项${NC}" ;;
        esac
    done
}

# ---------- 入口 ----------
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${GREEN}"
    echo "   ____                  _   __ _       _     _ "
    echo "  / ___|  ___  ___  ___| |_/ _(_) __ _| |__ | |"
    echo "  \___ \ / _ \/ _ \/ __| __| |_| |/ _\` | '_ \| |"
    echo "   ___) |  __/  __/ (__| |_|  _| | (_| | | | |_|"
    echo "  |____/ \___|\___|\___|\__|_| |_|\__, |_| |_(_)"
    echo "                                  |___/          "
    echo -e "${NC}"

    init_data
    init_class_info
    init_users
    do_login
    main_menu
fi
