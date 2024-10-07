
#!/bin/bash

echo "deleting old app"
sudo rm -rf /var/www/

echo "creating app folder"
sudo mkdir -p /var/www/cftc-app 

echo "moving files to app folder"
sudo mv  * /var/www/cftc-app

echo "Navigate to the app directory"
cd /var/www/cftc-app/

echo "installing python and pip"
sudo apt-get install -y python3 python3-pip

echo "install venv"
sudo apt install -y python3.12-venv

echo "create venv"
sudo python3 -m venv venv

echo "activating venv"
source venv/bin/activate

echo "check which python" 
which python3
which pip

echo "change ownership of file"
sudo chown -R ubuntu /var/www/cftc-app/


# Install application dependencies from requirements.txt
echo "Install application dependencies from requirements.txt"
pip install -r requirements.txt

echo "pip list"
pip list

# Update and install Nginx if not already installed
if ! command -v nginx > /dev/null; then
    echo "Installing Nginx"
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Configure Nginx to act as a reverse proxy if not already configured
if [ ! -f /etc/nginx/sites-available/myapp ]; then
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo bash -c 'cat > /etc/nginx/sites-available/myapp <<EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/cftc-app/myapp.sock;
    }
}
EOF'

    sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled
    sudo systemctl restart nginx
else
    echo "Nginx reverse proxy configuration already exists."
fi

echo "which pip"
which pip

echo "which gunicorn"
which gunicorn


echo "Stop any existing Gunicorn process"
sudo pkill gunicorn
sudo rm -rf myapp.sock

echo "which gunicorn"
which gunicorn

# # Start Gunicorn with the Flask application
# # Replace 'server:app' with 'yourfile:app' if your Flask instance is named differently.
# # gunicorn --workers 3 --bind 0.0.0.0:8000 server:app &
echo "starting gunicorn"
# sudo /var/www/cftc-app/venv/bin/gunicorn gunicorn -w 4 app_cftc:app
sudo /var/www/cftc-app/venv/bin/gunicorn --workers 3 --bind unix:myapp.sock app_cftc:server

echo "started gunicorn 🚀"