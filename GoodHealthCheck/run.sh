source ../../ghc-cvmfs-venv/bin/activate

if cmp -s /afs/cern.ch/work/r/rgargiul/last_pedestal_runs /afs/cern.ch/work/r/rgargiul/last_pedestal_runs_current ; then
    echo "File not changed on disk!"
    return 0
fi

runname=$(tail -n 1 /afs/cern.ch/work/r/rgargiul/last_pedestal_runs)

base="https://ecaltrg.web.cern.ch/ecaltrg/users/pierre/pedestals/2026"

found=0


while read -r prev; do
    url="${base}/${runname}_${prev}/"
    echo "Trying: $url"

    if ! curl -s "$url" | grep -q "404 - Not found"; then
        echo "FOUND: $url"
        found=1
        break
    fi
done < <(tac /afs/cern.ch/work/r/rgargiul/last_pedestal_runs | tail -n +2)

# if nothing found → exit sourced script
if [[ $found -eq 0 ]]; then
    echo "Pedestal analysis not found!"
    return 0
fi

cp /afs/cern.ch/work/r/rgargiul/last_pedestal_runs /afs/cern.ch/work/r/rgargiul/last_pedestal_runs_current

rm results/*.csv

python3 ghc.py --csv -o "results" -pon "$runname" $(date +"%d%m%Y") |& tee ghc.log

mv results/index.html results/index-page.html

week=$(date -d '+1 week' +%W)
day=$(date +%d-%B)

eos_pfg_performance_plots_2026="/eos/project/c/cms-ecalpfg2/www/PFGshifts/PERFORMANCE2026"
mkdir -p $eos_pfg_performance_plots_2026/week$week/$day

#cp -r results $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")

cd /afs/cern.ch/work/r/rgargiul/pfg-plots-upgrade

source get_runlist_for_plots_multiple_weeks.sh $(date -d '-2 week' +%W) $(date -d '+2 week' +%W) > rmshistory_runlist.csv

ch_st_run=$(awk -F, -v target=$runname 'NR>1 && $1>target {print $1}' rmshistory_runlist.csv | sort -n | head -n1)

python3 get_channel_status.py ${ch_st_run}

mv ch_status_${ch_st_run}.csv ../ghc/GoodHealthCheck/results

cd ../ghc/GoodHealthCheck/

python3 ghc_chstatus_matching.py results/ghc_$(date +"%d%m%Y")_bad_channels.csv results/ch_status_${ch_st_run}.csv > $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")/noisy_unflagged.txt

echo "tailing..."

channels=$(echo "["$(tail -n 1 $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")/noisy_unflagged.txt)"]")

echo "channels..."

echo $channels

cd /afs/cern.ch/work/r/rgargiul/pfg-plots-upgrade

mkdir -p $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")/rmshistories

python3 get_rms_history.py rmshistory_runlist.csv $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")/rmshistories "$channels"

cp $eos_pfg_performance_plots_2026/week$week/$day/index.php $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")/rmshistories


# Create the HTML mail file
echo -n "" > /tmp/rgargiul_ghc_mail.html

# Start HTML
echo "<html><body>" >> /tmp/rgargiul_ghc_mail.html
echo "<br><p> Good Health Check here:" $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y") "</p>" >> /tmp/rgargiul_ghc_mail.html
echo -n "<br><p>" >> /tmp/rgargiul_ghc_mail.html
cat $eos_pfg_performance_plots_2026/week$week/$day/GoodHealthCheck_$(date +"%d%m%Y")/noisy_unflagged.txt | sed ':a;N;$!ba;s/\n/<br>/g' >> /tmp/rgargiul_ghc_mail.html
echo -n "</p>" >> /tmp/rgargiul_ghc_mail.html
echo "</body></html>" >> /tmp/rgargiul_ghc_mail.html
TO="ruben.gargiulo@cern.ch"
SUBJECT="New GoodHealthCheck run on pedestal run: $runname"

BODY=$(cat /tmp/rgargiul_ghc_mail.html)

# Send email via sendmail
(
echo "To: $TO"
echo "Subject: $SUBJECT"
echo "MIME-Version: 1.0"
echo "Content-Type: text/html; charset=UTF-8"
echo ""
echo "$BODY"
) | /usr/sbin/sendmail -t

cd ../ghc/GoodHealthCheck/

