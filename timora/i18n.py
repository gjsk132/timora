LANGS = ("en", "ko")

STATE = {"lang": "en"}

STRINGS = {
    # --- units (used by fmt_dur) ---
    "u_h": {"en": "h", "ko": "시간"},
    "u_m": {"en": "m", "ko": "분"},
    "u_s": {"en": "s", "ko": "초"},

    # --- task label suffix ---
    "task_est_suffix": {"en": "   (est {dur})", "ko": "   (예상 {dur})"},

    # --- menu ---
    "quit": {"en": "Quit", "ko": "종료"},
    "manage": {"en": "Manage Tasks", "ko": "할 일 관리"},
    "add_tasks_menu": {"en": "Add Tasks (multiple)", "ko": "할 일 추가 (여러 개)"},
    "edit_task_menu": {"en": "Edit Task", "ko": "할 일 수정"},
    "delete_task_menu": {"en": "Delete Task", "ko": "할 일 삭제"},
    "no_active_tasks": {"en": "(No active tasks)", "ko": "(진행 중인 할 일 없음)"},
    "complete_task_menu": {"en": "Complete Task", "ko": "할 일 완료"},
    "reopen_task_menu": {"en": "Reopen Task", "ko": "완료 취소"},
    "status_resumed": {"en": "Resumed", "ko": "이어서 진행 중"},
    "status_inprogress": {"en": "In progress", "ko": "진행 중"},
    "stop_save": {"en": "Stop & Save", "ko": "종료하고 저장"},
    "cancel_nosave": {"en": "Cancel (don't save)", "ko": "취소 (저장 안 함)"},
    "detailed_view": {"en": "Detailed View", "ko": "상세 보기"},
    "progress_menu": {"en": "Progress (total)", "ko": "진행 현황 (누적)"},
    "today_menu": {"en": "Today's Summary", "ko": "오늘 요약"},
    "start_choose": {"en": "Start (choose a task)", "ko": "시작 (할 일 선택)"},
    "total_fmt": {"en": "Total {dur}", "ko": "총 누적 {dur}"},
    "add_first": {"en": "(Add one in 'Manage Tasks' first)", "ko": "(먼저 '할 일 관리'에서 추가)"},
    "edit_delete_records": {"en": "Edit/Delete Records", "ko": "기록 수정/삭제"},
    "no_saved_records": {"en": "(No saved records)", "ko": "(저장된 기록 없음)"},
    "language_menu": {"en": "Language", "ko": "언어"},
    "lang_en": {"en": "English", "ko": "English"},
    "lang_ko": {"en": "한국어", "ko": "한국어"},

    # --- settings ---
    "settings_menu": {"en": "Settings", "ko": "설정"},
    "notifications_toggle": {"en": "Notifications", "ko": "알림"},
    "away_toggle": {"en": "Away detection", "ko": "자리 비움 감지"},
    "away_threshold": {"en": "Away threshold", "ko": "자리 비움 기준"},
    "minutes": {"en": "{n} min", "ko": "{n}분"},
    "open_data_folder": {"en": "Open data folder", "ko": "데이터 폴더 열기"},

    # --- start label parts ---
    "total_part": {"en": "total {dur}", "ko": "총 누적 {dur}"},
    "est_part": {"en": "est {dur}", "ko": "예상 {dur}"},

    # --- stale session dialog ---
    "stale_title": {"en": "You have an unfinished session", "ko": "진행 중이던 기록이 있어요"},
    "stale_msg": {
        "en": "'{name}' started {dur} ago.\nThe app may have been closed during that time. What would you like to do?",
        "ko": "'{name}' 시작 후 {dur} 지났어요.\n앱이 꺼져 있던 시간도 포함됐을 수 있어요. 어떻게 할까요?"},
    "stale_save": {"en": "Save as is", "ko": "지금까지로 저장"},
    "stale_discard": {"en": "Discard", "ko": "버리기"},
    "stale_keep": {"en": "Keep going", "ko": "계속 진행"},

    # --- idle ---
    "idle_title": {"en": "Away detected", "ko": "자리 비움 감지"},
    "idle_sub": {"en": "'{name}' is still recording", "ko": "'{name}' 아직 기록 중이에요"},
    "idle_msg": {
        "en": "No input for a while. Press 'Stop & Save' to stop.",
        "ko": "한참 입력이 없네요. 멈추려면 '종료하고 저장'을 누르세요."},

    # --- tasks added ---
    "added_title": {"en": "Tasks added", "ko": "할 일 추가됨"},
    "added_msg": {"en": "{n} added", "ko": "{n}개 추가"},
    "added_dup": {"en": " · {n} duplicates skipped", "ko": " · 중복 {n}개 건너뜀"},

    # --- edit task ---
    "dup_title": {"en": "Duplicate name", "ko": "이름 중복"},
    "dup_msg": {"en": "'{name}' already exists.", "ko": "'{name}' 은(는) 이미 있는 할 일이에요."},

    # --- delete task ---
    "del_title": {"en": "Delete Task", "ko": "할 일 삭제"},
    "del_msg": {
        "en": "Remove '{name}' from the list?\n(Recorded time stays.)",
        "ko": "'{name}' 을(를) 목록에서 지울까요?\n(이미 기록된 시간은 그대로 남아요)"},
    "del_ok": {"en": "Delete", "ko": "삭제"},

    # --- complete task ---
    "completed_title": {"en": "Task completed 🎉", "ko": "할 일 완료 🎉"},
    "completed_msg": {"en": "Total {dur}{cmp} · Nice work!", "ko": "누적 {dur}{cmp} · 수고했어요!"},
    "completed_cmp": {"en": " · {pct}% of est {est}", "ko": " · 예상 {est} 대비 {pct}%"},

    # --- stop / save ---
    "saved_title": {"en": "Record saved", "ko": "기록 저장됨"},
    "saved_msg": {"en": "This session {dur} · total {total}{cmp} 👍", "ko": "이번 {dur} · 누적 {total}{cmp} 👍"},
    "stop_cmp": {"en": " · {pct}% of est {est}", "ko": " · 예상 {est} 대비 {pct}%"},
    "over_suffix": {"en": " ⚠️over", "ko": " ⚠️초과"},

    # --- progress summary ---
    "progress_title_plain": {"en": "Progress", "ko": "진행 현황"},
    "progress_none": {"en": "No recorded tasks yet.", "ko": "아직 기록된 할 일이 없어요."},
    "progress_title": {"en": "🎯 Progress (total)", "ko": "🎯 진행 현황 (누적)"},
    "prog_with_est": {"en": "actual {act} / est {est} · {pct}%", "ko": "실제 {act} / 예상 {est} · {pct}%"},
    "prog_no_est": {"en": "actual {act} · no estimate", "ko": "실제 {act} · 예상 미설정"},

    # --- today summary ---
    "today_title_plain": {"en": "Today's Summary", "ko": "오늘 요약"},
    "today_none": {"en": "No records today yet.", "ko": "오늘은 아직 기록이 없어요."},
    "today_total": {"en": "Total today {dur}", "ko": "오늘 총 {dur}"},
    "today_item": {"en": "{dur} · {pct}% of today", "ko": "{dur} · 오늘의 {pct}%"},
    "today_footer": {
        "en": "\n(See 'Progress' for totals vs estimates)",
        "ko": "\n(예상 대비 누적은 '진행 현황'에서 볼 수 있어요)"},
    "today_title": {"en": "📋 Today's Summary", "ko": "📋 오늘 요약"},

    # --- dialogs ---
    "ok": {"en": "OK", "ko": "확인"},
    "cancel": {"en": "Cancel", "ko": "취소"},
    "save": {"en": "Save", "ko": "저장"},
    "add": {"en": "Add", "ko": "추가"},
    "ph_task_name": {"en": "Task name", "ko": "할 일 이름"},
    "ph_est": {"en": "Estimated minutes  -  blank = none", "ko": "예상 소요시간(분) · 비우면 미설정"},
    "ph_actual": {"en": "Actual minutes", "ko": "실제 소요시간(분)"},
    "batch_title": {"en": "Add multiple tasks", "ko": "할 일 여러 개 추가"},
    "batch_info": {
        "en": ("One per line.   Format:  name, estimate(min)\n"
               "e.g.)  Memorize vocabulary, 30\n"
               "        Algorithm problems, 60\n"
               "        Walk            <- estimate is optional"),
        "ko": ("한 줄에 하나씩.   형식:  이름, 예상분\n"
               "예)  영어 단어 외우기, 30\n"
               "      알고리즘 문제, 60\n"
               "      산책            ← 예상분은 생략 가능")},
    "edit_task_title": {"en": "Edit Task", "ko": "할 일 수정"},
    "edit_record_title": {"en": "Edit Record", "ko": "기록 수정"},
    "edit_record_info": {
        "en": "Edit the actual minutes, or delete this record.",
        "ko": "실제 시간(분)을 고치거나, 이 기록을 삭제할 수 있어요."},
}


def set_language(lang):
    STATE["lang"] = lang if lang in LANGS else "en"


def get_language():
    return STATE["lang"]


def detect_default():
    try:
        from Foundation import NSLocale
        code = str(NSLocale.preferredLanguages()[0])
        if code.startswith("ko"):
            return "ko"
    except Exception:
        pass
    return "en"


def t(key, **kw):
    entry = STRINGS.get(key, {})
    s = entry.get(STATE["lang"]) or entry.get("en") or key
    return s.format(**kw) if kw else s
