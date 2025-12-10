from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import json
import os
import random
import io
import zipfile
from datetime import datetime
from num2words import num2words
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔥 Permitir que React (localhost:3000) se conecte al backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 en producción es mejor poner solo ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Función auxiliar para fechas
def fmt_fecha(valor, formato="%d/%m/%Y"):
    if pd.isna(valor) or valor == "":
        return None
    try:
        fecha = pd.to_datetime(valor, dayfirst=True, errors="coerce")
        if pd.isna(fecha):
            return valor
        return fecha.strftime(formato)
    except:
        return valor

def monto_a_letras_b(monto):
    try:
        monto_str = str(monto)
        if '.' in monto_str:
            partes = monto_str.split('.')
            entero = int(partes[0])
            decimal_str = partes[1]
            entero_letras = num2words(entero, lang='es')
            decimal_letras = " ".join(num2words(int(d), lang='es') for d in decimal_str)
            return f"{entero_letras} punto {decimal_letras}"
        else:
            return num2words(int(monto), lang='es')
    except:
        return None

def monto_a_letras(monto, moneda="dolares"):
    try:
        monto = float(monto)
        entero = int(monto)
        decimales = int(round((monto - entero) * 100))
        entero_letras = num2words(entero, lang='es')

        if moneda.lower() == "bolivares":
            if decimales > 0:
                return f"{entero_letras} con {num2words(decimales, lang='es')} céntimos"
            else:
                return f"{entero_letras} bolívares"
        elif moneda.lower() == "dolares":
            if decimales > 0:
                return f"{entero_letras} con {num2words(decimales, lang='es')} centavos"
            else:
                return f"{entero_letras}"
        else:
            return "Moneda no reconocida."
    except:
        return None

# 🔹 Transformar cada fila (copié la tuya)
def transformar_fila(row):
    fecha_emision = fmt_fecha(row["Fecha Emision"])
    fecha_vencimiento = fmt_fecha(row["Fecha Vencimiento"])
    fecha_pago = fmt_fecha(row["Fecha Pago"], "%d/%m/%Y")

    monto_bs = round(float(row["bolivares"]), 2)
    monto_usd = round(float(row["Total"]), 0)
    bolivares_sin_iva = round(float(row["bolivares sin iva"]), 2)
    precio_sin_iva = round(float(row["precio sin iva"]), 2)
    iva_bs = round(monto_bs - bolivares_sin_iva, 2)
    iva_usd = round(monto_usd - precio_sin_iva, 2)

    # 🔹 Generar navegación aleatoria
    navegacion1 = random.randint(1000, 6000)
    navegacion2 = random.randint(1000, 6000)
    navegacion3 = random.randint(1000, 6000)
    navegacion4 = random.randint(1000, 6000)
    navegacion5 = random.randint(1000, 6000)
    promedio = round((navegacion1 + navegacion2 + navegacion3 + navegacion4 + navegacion5 ) / 5, 0)

    return {
         "DocumentoElectronico": {
            "Encabezado": {
                "IdentificacionDocumento": {
                    "TipoDocumento": "01",
                    "NumeroDocumento": str(row["Correlativo"]),
                    "TipoProveedor": None,
                    "TipoTransaccion": None,
                    "NumeroPlanillaImportacion": None,
                    "NumeroExpedienteImportacion": None,
                    "SerieFacturaAfectada": None,
                    "NumeroFacturaAfectada": None,
                    "FechaFacturaAfectada": None,
                    "MontoFacturaAfectada": None,
                    "ComentarioFacturaAfectada": None,
                    "RegimenEspTributacion": None,
                    "FechaEmision": fecha_emision,
                    "FechaVencimiento": fecha_vencimiento,
                    "HoraEmision": "10:00:00 am",  # hora_emision,
                    "Anulado": False,
                    "TipoDePago": "Inmediato",
                    "Serie": "",
                    "Sucursal": "002",
                    "TipoDeVenta": "Interna",
                    "Moneda": "BSD",
                    "TransaccionId": f"FA{row['Correlativo']}",
                    "UrlPdf": None
                },
                "Vendedor": None,
                "Comprador": {
                    "TipoIdentificacion":str(row["Documento"]),
                    "NumeroIdentificacion": str(row["DNI/C.I./C.C./IFE"]),
                    "RazonSocial": row["Cliente"],
                    "Direccion": row["Dirección"],
                    "Ubigeo": None,
                    "Pais": "VE",
                    "Notificar": None,
                    "Telefono":[str(row["Telefono"])],
                    "Correo": [row["Correo"]],
                    "OtrosEnvios": None
                },
                "SujetoRetenido": None,
                "Tercero": None,
                "Totales": {
                    "NroItems": "1",
                    "MontoGravadoTotal": str(monto_bs),
                    "MontoExentoTotal": "0.00",
                    "MontoPercibidoTotal": "0.00",
                    "SubtotalAntesDescuento": str(bolivares_sin_iva),
                    "TotalDescuento": None,
                    "TotalRecargos": None,
                    "Subtotal": str(bolivares_sin_iva),
                    "TotalIVA": str(iva_bs),
                    "MontoTotalConIVA": str(monto_bs),
                    "TotalAPagar": str(monto_bs),
                    "MontoEnLetras":  monto_a_letras_b(monto_bs),
                    "ListaRecargo": None,
                    "ListaDescBonificacion": None,
                    "ImpuestosSubtotal": [
                        {
                            "CodigoTotalImp": "G",
                            "AlicuotaImp": "16.00",
                            "BaseImponibleImp": str(bolivares_sin_iva),
                            "ValorTotalImp": str(iva_bs)
                        }
                    ],
                    "FormasPago": [
                        {
                            "Descripcion": row["Forma de Pago"],
                            "Fecha": fecha_pago,
                            "Forma": "01",
                            "Monto": str(monto_bs),
                            "Moneda": "BSD",
                            "TipoCambio": "0.00"
                        }
                    ],
                    "TotalIGTF": None,
                    "TotalIGTF_VES": None
                },
                "TotalesRetencion": None,
                "TotalesOtraMoneda": {
                    "Moneda": "USD",
                    "TipoCambio": str(row["Tasa"]),
                    "MontoGravadoTotal": str(precio_sin_iva),
                    "MontoPercibidoTotal": "0.00",
                    "MontoExentoTotal": "0.00",
                    "Subtotal": str(precio_sin_iva),
                    "TotalAPagar": str(monto_usd),
                    "TotalIVA": str(iva_usd),
                    "MontoTotalConIVA": str(monto_usd),
                    "MontoEnLetras": monto_a_letras(monto_usd),
                    "SubtotalAntesDescuento": str(precio_sin_iva),
                    "TotalDescuento": None,
                    "TotalRecargos": None,
                    "ListaRecargo": None,
                    "ListaDescBonificacion": None,
                    "ImpuestosSubtotal": [
                        {
                            "CodigoTotalImp": "G",
                            "AlicuotaImp": "16.00",
                            "BaseImponibleImp": str(precio_sin_iva),
                            "ValorTotalImp": str(iva_usd)
                        }
                    ]
                },
                "Orden": None
            },
            "DetallesItems": [
                {
                    "NumeroLinea": "1",
                    "CodigoCIIU": None,
                    "CodigoPLU": "005",
                    "IndicadorBienoServicio": "2",
                    "Descripcion": row["Plan"],
                    "Cantidad": "1",
                    "UnidadMedida": "4L",
                    "PrecioUnitario": str(bolivares_sin_iva),
                    "PrecioUnitarioDescuento": None,
                    "MontoBonificacion": None,
                    "DescripcionBonificacion": None,
                    "DescuentoMonto": "0.00",
                    "RecargoMonto": "0",
                    "PrecioItem": str(bolivares_sin_iva),
                    "PrecioAntesDescuento":str(bolivares_sin_iva),
                    "CodigoImpuesto": "G",
                    "TasaIVA": "16",
                    "ValorIVA": str(iva_bs),
                    "ValorTotalItem":str(bolivares_sin_iva),
                    "InfoAdicionalItem": [],
                    "ListaItemOTI": None
                }
            ],
            "DetallesRetencion": None,
            "Viajes": None,
            "InfoAdicional": [
                {"Campo": "Contrato", "Valor": str(row["ID Servicio"])},
                {"Campo": "Mes1", "Valor": "JUL"},
                {"Campo": "Mes2", "Valor": "AGO"},
                {"Campo": "Mes3", "Valor": "SEP"},
                {"Campo": "Mes4", "Valor": "OCT"},
                {"Campo": "Mes5", "Valor": "NOV"},
                {"Campo": "Mes6", "Valor": "DIC"},
                {"Campo": "Cmes1", "Valor": str(navegacion1)},
                {"Campo": "Cmes2", "Valor": str(navegacion2)},
                {"Campo": "Cmes3", "Valor": str(navegacion3)},
                {"Campo": "Cmes4", "Valor": str(navegacion4)},
                {"Campo": "Cmes5", "Valor": str(navegacion5)},
                {"Campo": "Cmes6", "Valor": "0"},
                {"Campo": "Promedio", "Valor": str(int(promedio))},
            ],
            "GuiaDespacho": None,
            "Transporte": None,
            "EsLote": True,
            "EsMinimo": None
        }
    }

# 🔹 Endpoint para procesar el Excel
@app.post("/process_excel")
async def process_excel(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents)).fillna("")

    hoy = datetime.now().strftime("%Y%m%d")

    # 📦 Crear ZIP en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for idx, row in df.iterrows():
            data = transformar_fila(row)
            correlativo = str(row["Correlativo"]).zfill(6)

            lote_num = (idx // 100) + 1
            lote_nombre = f"J408185431-{hoy}-{str(lote_num).zfill(3)}"
            folder = f"FAC-{hoy}/{lote_nombre}/"

            filename = f"{folder}0{correlativo}.json"
            zf.writestr(filename, json.dumps(data, indent=4, ensure_ascii=False))

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=FAC-{hoy}.zip"}
    )

