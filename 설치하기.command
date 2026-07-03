#!/bin/bash
# 시간기록 앱 설치 스크립트 — 더블클릭으로 실행하세요.
set -e

# 이 스크립트가 있는 폴더로 이동 (폴더 이름/위치가 달라도 동작)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "================================================"
echo "  📕 시간기록 앱 설치를 시작합니다"
echo "  위치: $DIR"
echo "================================================"
echo ""

# 1) python3 확인
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 가 없습니다."
  echo "   터미널에서 아래 명령을 먼저 실행해 개발자 도구를 설치하세요:"
  echo ""
  echo "       xcode-select --install"
  echo ""
  echo "   설치가 끝나면 이 파일을 다시 더블클릭하세요."
  read -n 1 -s -r -p "엔터를 누르면 창이 닫힙니다..."
  exit 1
fi

# 2) 가상환경 생성 (이미 있으면 새로 만듦)
echo "🐍 파이썬 가상환경을 만드는 중..."
rm -rf venv
python3 -m venv venv

# 3) 패키지 설치
echo "📦 필요한 패키지를 설치하는 중... (1~2분 걸릴 수 있어요)"
./venv/bin/python -m pip install --upgrade pip >/dev/null
./venv/bin/pip install -r requirements.txt

# 4) 앱 실행 경로를 이 폴더로 맞춰줌
RUN="시간기록.app/Contents/MacOS/run"
if [ -f "$RUN" ]; then
  cat > "$RUN" <<EOF
#!/bin/bash
# .app로 직접 exec 하면 메뉴바 슬롯이 배정되지 않아, 파이썬을 백그라운드로 분리 실행한다.
DIR="$DIR"
cd "\$DIR" || exit 1
nohup "\$DIR/venv/bin/python" "\$DIR/tracker.py" >/dev/null 2>&1 &
exit 0
EOF
  chmod +x "$RUN"
fi

echo ""
echo "================================================"
echo "  ✅ 설치 완료!"
echo ""
echo "  실행 방법:"
echo "   • '시간기록.app' 을 더블클릭하면 메뉴바에 📕 가 나타납니다."
echo "   • 자주 쓰려면 Dock이나 응용 프로그램 폴더에 넣어두세요."
echo "================================================"
echo ""
read -n 1 -s -r -p "엔터를 누르면 창이 닫힙니다..."
