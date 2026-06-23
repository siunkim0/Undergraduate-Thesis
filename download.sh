# The Data Path of 2016H SingleMuon
# https://opendata.cern.ch/record/30563

# 파일 리스트 저장
cernopendata-client get-file-locations --recid 30563 --protocol xrootd > filelist_SingleMuon_2016H.txt

# 저장 디렉토리 생성
mkdir -p SingleMuon_2016H

# 백그라운드로 일괄 다운로드 (nohup으로 세션 끊겨도 계속)
nohup bash -c '
count=0
total=$(wc -l < filelist_SingleMuon_2016H.txt)
while read -r url; do
    count=$((count+1))
    fname=$(basename "$url")
    if [ -f "SingleMuon_2016H/$fname" ]; then
        echo "[$count/$total] Skip (exists): $fname"
        continue
    fi
    echo "[$count/$total] Downloading: $fname"
    xrdcp "$url" ./SingleMuon_2016H/
done < filelist_SingleMuon_2016H.txt
' > download.log 2>&1 &

# 진행 상황 확인
tail -f download.log
