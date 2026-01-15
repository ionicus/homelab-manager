# Test Nodes for Automation Testing

Docker-based SSH nodes for testing homelab-manager automation features.

## Quick Start

```bash
cd docker/test-nodes
docker compose up -d --build
```

## Nodes

| Node    | IP Address   | Hostname |
|---------|--------------|----------|
| node1   | 172.28.0.10  | node1    |
| node2   | 172.28.0.11  | node2    |
| node3   | 172.28.0.12  | node3    |

## Credentials

| User    | Password    | Sudo Access |
|---------|-------------|-------------|
| root    | rootpass    | N/A         |
| ansible | ansible123  | NOPASSWD    |

## Test SSH Access

```bash
# As root
ssh root@172.28.0.10
# Password: rootpass

# As ansible user
ssh ansible@172.28.0.10
# Password: ansible123
```

## Backend Configuration

Add these to `backend/.env`:

```bash
# Password authentication (easiest for testing)
ANSIBLE_USER=ansible
ANSIBLE_PASSWORD=ansible123
ANSIBLE_HOST_KEY_CHECKING=no
```

**Note:** Password auth requires `sshpass` installed:
```bash
# Debian/Ubuntu
sudo apt install sshpass

# macOS
brew install hudochenkov/sshpass/sshpass
```

## Add Devices to Homelab Manager

Add these devices in the UI or via API:

1. **Node 1**: IP `172.28.0.10`, Name `test-node1`
2. **Node 2**: IP `172.28.0.11`, Name `test-node2`
3. **Node 3**: IP `172.28.0.12`, Name `test-node3`

## Commands

```bash
# Start nodes
docker compose up -d --build

# Stop nodes
docker compose down

# View logs
docker compose logs -f

# Rebuild after Dockerfile changes
docker compose up -d --build --force-recreate

# Remove everything including network
docker compose down -v --remove-orphans
```

## SSH Key Authentication (Optional)

To use SSH keys instead of passwords:

```bash
# Generate key (if you don't have one)
ssh-keygen -t ed25519 -f ~/.ssh/homelab_test -N ""

# Copy to nodes
ssh-copy-id -i ~/.ssh/homelab_test ansible@172.28.0.10
ssh-copy-id -i ~/.ssh/homelab_test ansible@172.28.0.11
ssh-copy-id -i ~/.ssh/homelab_test ansible@172.28.0.12

# Set in backend environment
export ANSIBLE_SSH_KEY=~/.ssh/homelab_test
```
