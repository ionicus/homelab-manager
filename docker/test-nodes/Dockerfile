# Test node for homelab-manager automation testing
# Provides SSH access with both root and user accounts for Ansible

FROM ubuntu:22.04

ARG ROOT_PASSWORD=rootpass
ARG USER_NAME=ansible
ARG USER_PASSWORD=ansible123

ENV DEBIAN_FRONTEND=noninteractive

# Install SSH server, Python (Ansible requirement), sudo, and common utilities
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-apt \
    sudo \
    curl \
    wget \
    vim \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /var/run/sshd

# Configure SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Set root password
RUN echo "root:${ROOT_PASSWORD}" | chpasswd

# Create ansible user with sudo privileges
RUN useradd -m -s /bin/bash ${USER_NAME} \
    && echo "${USER_NAME}:${USER_PASSWORD}" | chpasswd \
    && usermod -aG sudo ${USER_NAME} \
    && echo "${USER_NAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USER_NAME}

# Create .ssh directories for both users
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh \
    && mkdir -p /home/${USER_NAME}/.ssh && chmod 700 /home/${USER_NAME}/.ssh \
    && chown -R ${USER_NAME}:${USER_NAME} /home/${USER_NAME}/.ssh

# Expose SSH port
EXPOSE 22

# Start SSH daemon
CMD ["/usr/sbin/sshd", "-D"]
