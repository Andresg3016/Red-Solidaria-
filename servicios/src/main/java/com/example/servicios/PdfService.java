package com.example.servicios;

import com.itextpdf.io.image.ImageDataFactory;
import com.itextpdf.kernel.colors.DeviceRgb;
import com.itextpdf.kernel.events.Event;
import com.itextpdf.kernel.events.IEventHandler;
import com.itextpdf.kernel.events.PdfDocumentEvent;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfPage;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.kernel.pdf.canvas.PdfCanvas;
import com.itextpdf.kernel.pdf.colorspace.PdfDeviceCs;
import com.itextpdf.kernel.pdf.colorspace.PdfShading;
import com.itextpdf.kernel.geom.Rectangle;
import com.itextpdf.layout.Canvas;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Image;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.HorizontalAlignment;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.layout.properties.UnitValue;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.util.Map;

@Service
public class PdfService {

    public byte[] generarReporte(EmailRequest datos) {
            // Logs de depuración para verificar los datos recibidos desde Python
            System.out.println("DEBUG JAVA - Categoría recibida de Python: " + datos.getCategoriaFiltrada());
            System.out.println("DEBUG JAVA - Estado recibido de Python: " + datos.getEstadoFiltrado());
            System.out.println("DEBUG JAVA - Cantidad de donaciones recibidas: " + (datos.getDonaciones() != null ? datos.getDonaciones().size() : 0));
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        
        try {
            PdfWriter writer = new PdfWriter(out);
            PdfDocument pdf = new PdfDocument(writer);
            
            // --- AGREGAMOS EL MANEJADOR DEL PIE DE PÁGINA ---
            pdf.addEventHandler(PdfDocumentEvent.END_PAGE, new FooterHandler());

            Document document = new Document(pdf);
            // Margen inferior aumentado para que el contenido no pise el pie de página
            document.setBottomMargin(50); 

            // Colores exactos
            float[] colorAzul = new float[]{30f/255f, 82f/255f, 255f/255f};   // #1e52ff
            float[] colorVerde = new float[]{99f/255f, 255f/255f, 94f/255f}; // #63ff5e
            DeviceRgb grisFondo = new DeviceRgb(248, 249, 250);

            // --- BLOQUE DE ENCABEZADO CON DEGRADADO ---
            PdfCanvas canvas = new PdfCanvas(pdf.addNewPage());
            float width = pdf.getDefaultPageSize().getWidth();
            float height = pdf.getDefaultPageSize().getHeight();
            
            Rectangle headerRect = new Rectangle(0, height - 150, width, 150);

            PdfShading.Axial axial = new PdfShading.Axial(new PdfDeviceCs.Rgb(), 
                                    headerRect.getLeft(), headerRect.getBottom(), colorAzul, 
                                    headerRect.getRight(), headerRect.getBottom(), colorVerde);
            
            canvas.saveState()
                  .rectangle(headerRect)
                  .clip()
                  .endPath()
                  .paintShading(axial)
                  .restoreState();

            // --- CONTENIDO SOBRE EL ENCABEZADO ---
            try {
                ClassPathResource res = new ClassPathResource("static/images/logo.jpeg");
                Image logo = new Image(ImageDataFactory.create(res.getURL().getPath()));
                logo.setMaxHeight(65);
                logo.setHorizontalAlignment(HorizontalAlignment.CENTER);
                logo.setMarginTop(10);
                logo.setBackgroundColor(DeviceRgb.WHITE);
                logo.setPadding(8);
                document.add(logo);
            } catch (Exception e) {
                System.out.println("Logo no encontrado");
            }

            document.add(new Paragraph("RED SOLIDARIA")
                .setFontColor(DeviceRgb.WHITE)
                .setTextAlignment(TextAlignment.CENTER)
                .setBold()
                .setFontSize(26)
                .setMarginTop(5));

            document.add(new Paragraph("Reporte de Impacto de Donaciones")
                .setFontColor(DeviceRgb.WHITE)
                .setTextAlignment(TextAlignment.CENTER)
                .setFontSize(13)
                .setMarginBottom(45));

            // --- TABLA DE INFORMACIÓN ---
            Table infoTable = new Table(UnitValue.createPercentArray(new float[]{1, 1})).useAllAvailableWidth();
            infoTable.setBackgroundColor(grisFondo).setPadding(10).setMarginBottom(20);
            
            String nombreDonante = datos.getNombreFundacion();
            boolean esDonante = false;
            // Si el nombre de fundación es null o vacío, intentamos obtener el nombre del donante
            if (nombreDonante == null || nombreDonante.equalsIgnoreCase("null") || nombreDonante.trim().isEmpty()) {
                try {
                    java.lang.reflect.Method m = datos.getClass().getMethod("getNombreDonador");
                    Object nombre = m.invoke(datos);
                    if (nombre != null && !nombre.toString().trim().isEmpty()) {
                        nombreDonante = nombre.toString();
                        esDonante = true;
                    }
                } catch (Exception e) { /* Ignorar si no existe */ }
            }
            if (!esDonante) {
                infoTable.addCell(new Cell().add(new Paragraph("Fundación: " + nombreDonante).setBold()).setBorder(com.itextpdf.layout.borders.Border.NO_BORDER));
                infoTable.addCell(new Cell().add(new Paragraph("NIT: " + datos.getNit()).setTextAlignment(TextAlignment.RIGHT)).setBorder(com.itextpdf.layout.borders.Border.NO_BORDER));
            } else {
                infoTable.addCell(new Cell(1, 2).add(new Paragraph("Donante: " + nombreDonante).setBold()).setBorder(com.itextpdf.layout.borders.Border.NO_BORDER));
            }
            
            String categoriaFiltro = (datos.getCategoriaFiltrada() != null && !datos.getCategoriaFiltrada().isEmpty()) ? datos.getCategoriaFiltrada() : "Todas";
            String estado = (datos.getEstadoFiltrado() != null && !datos.getEstadoFiltrado().isEmpty()) ? datos.getEstadoFiltrado() : "Todos";
            infoTable.addCell(new Cell().add(new Paragraph("Filtro Categoría: " + categoriaFiltro + "\nFiltro Estado: " + estado)).setBorder(com.itextpdf.layout.borders.Border.NO_BORDER));
            infoTable.addCell(new Cell().add(new Paragraph("Total Registros: " + datos.getCantidadDonaciones()).setBold().setTextAlignment(TextAlignment.RIGHT)).setBorder(com.itextpdf.layout.borders.Border.NO_BORDER));
            
            document.add(infoTable);

            // --- TABLA DE DATOS ---

            Table table = new Table(new float[]{140f, 100f, 120f, 120f, 100f}).useAllAvailableWidth();
            table.addHeaderCell(new Cell().add(new Paragraph("Fundación").setBold().setFontColor(DeviceRgb.WHITE)).setBackgroundColor(new DeviceRgb(30, 82, 255)));
            table.addHeaderCell(new Cell().add(new Paragraph("Categoría").setBold().setFontColor(DeviceRgb.WHITE)).setBackgroundColor(new DeviceRgb(30, 82, 255)));
            table.addHeaderCell(new Cell().add(new Paragraph("Descripción").setBold().setFontColor(DeviceRgb.WHITE)).setBackgroundColor(new DeviceRgb(30, 82, 255)));
            table.addHeaderCell(new Cell().add(new Paragraph("Cantidad").setBold().setFontColor(DeviceRgb.WHITE)).setBackgroundColor(new DeviceRgb(30, 82, 255)).setTextAlignment(TextAlignment.CENTER));
            table.addHeaderCell(new Cell().add(new Paragraph("Estado").setBold().setFontColor(DeviceRgb.WHITE)).setBackgroundColor(new DeviceRgb(30, 82, 255)).setTextAlignment(TextAlignment.CENTER));

            if (datos.getDonaciones() != null && !datos.getDonaciones().isEmpty()) {
                for (Map<String, Object> d : datos.getDonaciones()) {
                    String fundacion = d.get("fundacion_nombre") != null ? d.get("fundacion_nombre").toString() : "-";
                    String categoria = d.get("nombre_categoria") != null ? d.get("nombre_categoria").toString() : "-";
                    String descripcion = d.get("descripcion") != null ? d.get("descripcion").toString() : "-";
                    String cantidad = d.get("cantidad") != null ? d.get("cantidad").toString() : "0";
                    String estadoFundacion = d.get("estado") != null && !d.get("estado").toString().isEmpty()
                        ? d.get("estado").toString()
                        : (d.get("estado_fundacion") != null && !d.get("estado_fundacion").toString().isEmpty() ? d.get("estado_fundacion").toString() : "-");
                    table.addCell(new Cell().add(new Paragraph(fundacion)).setPadding(5));
                    table.addCell(new Cell().add(new Paragraph(categoria)).setPadding(5));
                    table.addCell(new Cell().add(new Paragraph(descripcion)).setPadding(5));
                    table.addCell(new Cell().add(new Paragraph(cantidad)).setTextAlignment(TextAlignment.CENTER));
                    table.addCell(new Cell().add(new Paragraph(estadoFundacion)).setTextAlignment(TextAlignment.CENTER));
                }
            } else {
                table.addCell(new Cell(1, 5).add(new Paragraph("No se encontraron donaciones con los filtros seleccionados.")).setPadding(5));
            }

            document.add(table);
            document.close();
            
        } catch (Exception e) {
            e.printStackTrace();
        }
        return out.toByteArray();
    }

    // --- CLASE INTERNA PARA EL PIE DE PÁGINA FIJO ---
    private class FooterHandler implements IEventHandler {
        @Override
        public void handleEvent(Event event) {
            PdfDocumentEvent docEvent = (PdfDocumentEvent) event;
            PdfDocument pdf = docEvent.getDocument();
            PdfPage page = docEvent.getPage();
            
            Rectangle pageSize = page.getPageSize();
            PdfCanvas pdfCanvas = new PdfCanvas(page);
            Canvas canvas = new Canvas(pdfCanvas, pageSize);

            // Dibujamos el texto en la parte inferior (y = 20)
            canvas.showTextAligned(new Paragraph("© 2026 Red Solidaria - Uniendo corazones.")
                    .setFontSize(10)
                    .setFontColor(new DeviceRgb(120, 120, 120)),
                    pageSize.getWidth() / 2, 20, TextAlignment.CENTER);
            
            canvas.close();
        }
    }
}