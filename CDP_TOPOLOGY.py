from netmiko import ConnectHandler
import networkx as nx
import matplotlib.pyplot as plt

visited_devices = set()

topology_links = []

def discover_neighbors(device):
    ip = device["host"]

    if ip in visited_devices:
        return

    print(f"\n Conectando a {ip}...")
    visited_devices.add(ip)

    try:
        connection = ConnectHandler(**device)
        connection.enable()

        output = connection.send_command("show cdp neighbors detail", use_textfsm=True)
        local_hostname = connection.find_prompt().replace("#", "").strip()
        local_hostname = local_hostname.replace(".local", "").lower()
        print(output)
        
        for neighbor in output:
            neighbor_ip = neighbor.get("mgmt_address")
            neighbor_id = neighbor.get("neighbor_name")
            if neighbor_id:
                neighbor_id = neighbor_id.replace(".local", "").lower()
            platform = neighbor.get("platform")
            port = neighbor.get("local_interface")
            remote_port = neighbor.get("neighbor_interface")

            if neighbor_ip and neighbor_id:
                print(f" Vecino detectado: {neighbor_id} ({neighbor_ip}) en {port}")

                topology_links.append({
                    "local_device": local_hostname,
                    "local_port": port,
                    "remote_device": neighbor_id,
                    "remote_port" : remote_port
                })

                # preparar el siguiente salto
                neighbor_device = {
                    "device_type" : "cisco_ios",
                    "host": neighbor_ip,
                    "username": device["username"],
                    "password": device["password"],
                    "secret": device["secret"],
                }

                print(neighbor_device)
                # exploracion recursiva
                discover_neighbors(neighbor_device)

        connection.disconnect()

    except Exception as e:
        print(f"No se pudo conectar a {ip}: {e}")
# Dispositivo de inicio
start_device = {
    "device_type": "cisco_ios",
    "username": "admin",
    "password": "admin123",
    "secret": "enable123",
    "host": "192.168.1.5",
}

# inicio de descubrimiento
print("Iniciando descubrimiento de vecinos por CDP")
discover_neighbors(start_device)

print("\n Descubrimiento terminado")
for link in topology_links:
    print(f" {link['local_device']} ({link['local_port']}) ⇄ ({link['remote_port']}) {link['remote_device']}")
def abreviar_interface(nombre):
    if nombre.startswith("GigabitEthernet"):
        return nombre.replace("GigabitEthernet", "Gi")
    elif nombre.startswith("FastEthernet"):
        return nombre.replace("FastEthernet", "Fa")
    else:
        return nombre

G = nx.Graph()
edge_labels = {}

#conexiones del grafo
for link in topology_links:
    local_device = link['local_device']
    remote_device = link['remote_device']
    local_port = link['local_port']
    remote_port = link['remote_port']

    G.add_edge(local_device, remote_device)

    #etiquetas bidireccionales
    edge_labels[(local_device, remote_device)] = f"{abreviar_interface(local_port)} \u21C4 {abreviar_interface(remote_port)}"

#diseño del grafo
plt.figure(figsize=(10,7))
pos = nx.spring_layout(G, k=0.8)

#modos de borde y etiquetas
nx.draw_networkx_nodes(G, pos, node_size=2500, node_color="lightsteelblue", edgecolors="black")
nx.draw_networkx_edges(G, pos, width=2)
nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

#dibujar etiquetas de los bordes
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, label_pos=0.5)

#título y ocultar ejes
plt.title("Topología de red Descubierta", fontsize=14)
plt.axis('off')