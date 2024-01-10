# Use the official Kali Linux base image
FROM kalilinux/kali-rolling

# Set environment variable for Kali user password
ENV PWD=123

# Update the package list and install necessary packages
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wget \
    kali-linux-headless \
    xorg \
    xrdp \
    kali-desktop-xfce \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade the installed packages
RUN apt-get update && apt-get --yes --force-yes full-upgrade

# Configure xrdp to use port 3390
RUN sed -i 's/port=3389/port=3390/g' /etc/xrdp/xrdp.ini

# Start xrdp service
CMD ["/etc/init.d/xrdp", "start"]

# Create a non-root user 'kali' and add to sudo group
RUN useradd -m -s /bin/bash -G sudo kali

# Set the password for the 'kali' user
RUN echo "kali:$PWD" | chpasswd

# Set up home directory for the 'kali' user
USER kali
WORKDIR /home/kali

# Expose the default xrdp port
EXPOSE 3390
