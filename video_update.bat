D:
call C:\Users\23711\Miniconda3\Scripts\activate.bat C:\Users\23711\Miniconda3
call conda activate base
cd /d D:\dream_life\data-management\video
python get_video_ls.py
cd /d D:\dream_life\data-management
git branch
git pull origin main
git add .
git commit -m "auto: update data and web"
git push origin main
pause
