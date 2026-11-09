"""Visualizacoes auxiliares; nenhum algoritmo de grafos e terceirizado."""
import math
import folium
import matplotlib.pyplot as plt


def montar_mapa(df, matriz, rota=None, geom=None, geom_real=False, mostrar_arestas=False):
    pontos = df.to_dict("records")
    media_lat = sum(p["latitude"] for p in pontos) / len(pontos)
    media_lon = sum(p["longitude"] for p in pontos) / len(pontos)
    mapa = folium.Map(location=(media_lat, media_lon), zoom_start=12, tiles="OpenStreetMap", control_scale=True)
    if mostrar_arestas and len(df) <= 12:
        for i in range(len(matriz)):
            for j in range(i + 1, len(matriz)):
                if math.isfinite(matriz[i][j]):
                    folium.PolyLine([[pontos[i]["latitude"], pontos[i]["longitude"]],
                                     [pontos[j]["latitude"], pontos[j]["longitude"]]],
                                    color="#aeb9cc", weight=1.7, opacity=0.35,
                                    tooltip=f"Ligacao {i}-{j}: {matriz[i][j]:.2f} km (peso)").add_to(mapa)
    for i, p in enumerate(pontos):
        folium.Marker(location=(p["latitude"],p["longitude"]),
                      icon=folium.DivIcon(html=(f'<div style="background:{"#147d64" if i == 0 else "#183d79"};'
                                              'color:white;border:2px solid white;border-radius:50%;'
                                              'box-shadow:0 1px 6px #333;padding:5px;min-width:22px;'
                                              f'text-align:center;font-weight:700">{i}</div>')),
                      tooltip=f'{i} · {p["nome"]}', popup=folium.Popup(p["nome"], max_width=300)).add_to(mapa)
    if rota:
        if geom:
            folium.PolyLine(geom, color="#f26a36", weight=5, opacity=0.9,
                            tooltip="Rota por ruas OSRM" if geom_real else "Ligacao ilustrativa").add_to(mapa)
        else:
            for a,b in zip(rota, rota[1:]):
                folium.PolyLine([[pontos[a]["latitude"], pontos[a]["longitude"]],
                                 [pontos[b]["latitude"], pontos[b]["longitude"]]],
                                color="#f26a36", weight=5, opacity=.88,
                                dash_array="7 5", tooltip="Linha reta de visualizacao; nao representa ruas").add_to(mapa)
    folium.LayerControl().add_to(mapa)
    return mapa


def figura_esquematica(df, matriz, rota=None):
    """Mapa esquematico, independente de tiles e de conexao."""
    pontos = df.to_dict("records")
    fig, ax = plt.subplots(figsize=(9, 4.7))
    for i in range(len(pontos)):
        for j in range(i + 1, len(pontos)):
            if math.isfinite(matriz[i][j]) and len(pontos) <= 12:
                ax.plot([pontos[i]["longitude"],pontos[j]["longitude"]],
                        [pontos[i]["latitude"],pontos[j]["latitude"]], color="#d8e0e9", lw=.8, zorder=1)
    if rota:
        for a,b in zip(rota,rota[1:]):
            ax.annotate("", xy=(pontos[b]["longitude"],pontos[b]["latitude"]),
                        xytext=(pontos[a]["longitude"],pontos[a]["latitude"]),
                        arrowprops={"arrowstyle": "->", "color": "#e86831", "lw": 2.2}, zorder=3)
    for i,p in enumerate(pontos):
        ax.scatter(p["longitude"],p["latitude"],s=115 if i==0 else 74,
                   color="#147d64" if i==0 else "#244c87", zorder=4)
        ax.annotate(str(i), (p["longitude"],p["latitude"]),xytext=(4,5),textcoords="offset points",fontsize=9)
    ax.set_xlabel("Longitude (esquema geografico)")
    ax.set_ylabel("Latitude")
    ax.set_title("Grafo e rota · linhas nao representam trajeto pelas ruas", fontsize=10)
    ax.grid(alpha=.15)
    fig.tight_layout()
    return fig
