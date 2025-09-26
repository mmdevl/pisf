# PISF (Personal IMAP Spam Filter)

## Dependencies

For systems like Alma Linux, CentOS, RHEL:

```bash
# install spamassassin
dnf -y install spamassassin
# update once manually
sa-update
# activate and start
systemctl enable spamassassin.service --now
```

For macOS (just for testing):

```bash
# install spamassassin with macports
port install p5-mail-spamassassin
# update manually
umask 22
sa-update-5.34
# start
spamd-5.34
```

## Installation

```bash
git clone https://github.com/mmdevl/pisf /scratch/pisf
python -m venv /scratch/pisf
source /scratch/pisf/bin/activate
pip install -r /scratch/pisf/requirements.txt
```

## Configuration

```bash
cd /scratch/pisf
cp -p pisf.conf-dist pisf.conf
```

and personalise at least the "IMAP" stuff.

### Start

For systems like Alma Linux, CentOS, RHEL:

```bash
cp /scratch/pisf/src/pisf.service /etc/systemd/system/pisf.service
systemctl enable pisf.service --now
```

For macOS (just for testing):

```bash
/scratch/pisf/bin/python /scratch/pisf/personal-imap-spam-filter.py
```

## Cronjob

Add the following cronjob:

```
@daily          /scratch/pisf/bin/python /scratch/pisf/learn-imap-spam.py
```
