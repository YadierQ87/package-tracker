from odoo import models

class ContenedorReport(models.AbstractModel):
    _name = 'report.esp_componedor_paquetes.contenedor_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Container XLSX Report"

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            # One sheet by partner
            worksheet = workbook.add_worksheet("FORMULARIO")
            bold = workbook.add_format({'bold': True})
            border = workbook.add_format({'border': True})
            worksheet.write("F2:R2", "INFORMACION ADELANTADA MANIFIESTO DE ENVIOS  DE ORIGEN",border)
            worksheet.write("A4:B4", "Operador",bold)
            worksheet.write("A5:B5", "No.Guía Aérea / No.Contenedor",border)
            worksheet.write("A6:B6", "No.Vuelo / No.BL",border)
            worksheet.write("A7", "Línea Aérea / Naviera",border)
            worksheet.write("A8", "País Origen",border)
            worksheet.write("A9", "Cant. Envíos",border)
            worksheet.write("A10", "Peso en KG",border)
            worksheet.write("H4", "No. ENVIO",border)
            worksheet.write("H5", "CAN.BULTOS",border)
            worksheet.write("H10", "AGENCIA",border)
            #datos del envio
            worksheet.write("A13", "DATOS ", border)
            worksheet.write("F13", "DATOS ",border)
            worksheet.write("W13", "DATOS DEL REMITENTE",border)
            #escribir los datos
            worksheet.write("B4", obj.name)#operator
            worksheet.write("B5", obj.hbl_bl_code)#no guia area
            worksheet.write("B6", obj.trip_number)#no vuelo o hbl
            worksheet.write("B7", obj.vessel.name)#linea area o naiera
            worksheet.write("B8", obj.shipment_origin.country_id.name)#pais origen
            worksheet.write("B9", len(obj.envoys_total_ids))#cantd envios
            worksheet.write("B10", obj.total_weight)#peso kg
            worksheet.write("H6", obj.total_bags)#cantd bultos
            worksheet.write("H11", obj.forwarder.name)#agencia
            worksheet.write("B13", "DEL",border)
            worksheet.write("C13", "ENVIO",border)
            worksheet.write("G13", "DEL ",border)
            worksheet.write("H13", "DESTINATARIO ",border)
            # datos del envio
            worksheet.write("A14", "CODIGO")
            worksheet.write("B14", "PESO")
            worksheet.write("C14", "PAIS")
            worksheet.write("D14", "DESCRIPCION")
            worksheet.write("E14", "FECHA")
            worksheet.write("A14", "ENVIO")
            worksheet.write("B14", "KGS")
            worksheet.write("C14", "ORIGEN")
            worksheet.write("D14", "CONTENIDO")
            worksheet.write("E14", "IMPOSICION")
            # datos del destinatario
            worksheet.write("F14", "Primer")
            worksheet.write("G14", "Segundo")
            worksheet.write("H14", "Primer")
            worksheet.write("I14", "Segundo")
            worksheet.write("J14", "Carnet")
            worksheet.write("K14", "Pasaporte")
            worksheet.write("L14", "Nacionalidad")
            worksheet.write("M14", "Fecha")
            worksheet.write("N14", "Telefono")
            worksheet.write("O14", "Calle")
            worksheet.write("P14", "Entre")
            worksheet.write("Q14", "Numero")
            worksheet.write("R14", "Apto")
            worksheet.write("S14", "Piso")
            worksheet.write("T14", "Provincia")
            worksheet.write("U14", "Municipio")
            # datos del destinatario 2 bloque
            worksheet.write("F15", "Nombre")
            worksheet.write("G15", "Nombre")
            worksheet.write("H15", "Apellido")
            worksheet.write("I15", "Apellido")
            worksheet.write("J15", "Identidad")
            worksheet.write("M15", "Nacimiento")
            #datos del remitente
            worksheet.write("V14", "Primer")
            worksheet.write("W14", "Segundo")
            worksheet.write("X14", "Primer")
            worksheet.write("Y14", "Segundo")
            worksheet.write("Z14", "Nacionalidad")
            worksheet.write("AA14", "Fecha")
            worksheet.write("V15", "Nombre")
            worksheet.write("W15", "Nombre")
            worksheet.write("X15", "Apellido")
            worksheet.write("Y15", "Apellido")
            worksheet.write("AA15", "Nacimiento")
            for envio_total in obj.envoys_total_ids:
                for envio in envio_total.envoy_ids:
                    # datos del envio
                    worksheet.write("A16", envio.name)
                    worksheet.write("B16", envio.weight)
                    worksheet.write("C16", envio.destination.country_id.name)#pais origen
                    worksheet.write("D16", "DESCRIPCION")#contenido
                    worksheet.write("E16", "FECHA")#fecha imposicion
                    # datos del destinatario
                    worksheet.write("F16", envio.destination.name)
                    worksheet.write("G16", envio.destination.second_name)
                    worksheet.write("H16", envio.destination.first_lastname)
                    worksheet.write("I16", envio.destination.second_lastname)
                    worksheet.write("J16", envio.destination.ci)
                    worksheet.write("K16", envio.destination.passport)
                    worksheet.write("L16", envio.destination.nacionality)
                    worksheet.write("M16", envio.destination.date_of_birth)#nacimiento
                    worksheet.write("N16", envio.destination.phone)
                    worksheet.write("O16", envio.destination.street)
                    worksheet.write("P16", envio.destination.street2)
                    worksheet.write("Q16", envio.destination.num_house)
                    worksheet.write("R16", "-" )
                    worksheet.write("S16", "-")
                    worksheet.write("T16", envio.destination.state_id.name)
                    worksheet.write("U16", envio.destination.city)
                    # datos del remitente
                    worksheet.write("V16", envio.sender.name)
                    worksheet.write("W16", envio.sender.second_name)
                    worksheet.write("X16", envio.sender.first_lastname)
                    worksheet.write("Y16", envio.sender.second_lastname)
                    worksheet.write("Z16", envio.sender.nacionality)
                    worksheet.write("AA16", envio.sender.date_of_birth)
