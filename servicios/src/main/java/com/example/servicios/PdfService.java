package com.example.servicios;

import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.Document;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import org.springframework.stereotype.Service;
import java.io.ByteArrayOutputStream;
import java.util.Map;

@Service
public class PdfService {

    public byte[] generarReporte(EmailRequest datos) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        PdfWriter writer = new PdfWriter(out);
        PdfDocument pdf = new PdfDocument(writer);
        Document document = new Document(pdf);

        document.add(new Paragraph("RED SOLIDARIA")
                .setTextAlignment(TextAlignment.CENTER)
                .setBold().setFontSize(22));

        document.add(new Paragraph("Reporte de Impacto de Donaciones")
                .setTextAlignment(TextAlignment.CENTER).setFontSize(14));

        document.add(new Paragraph("\n"));
        document.add(new Paragraph("Fundación: " + datos.getNombreFundacion()).setBold());
        document.add(new Paragraph("NIT: " + datos.getNit()));
        document.add(new Paragraph("Resumen: " + datos.getCantidadDonaciones() + " registros encontrados."));
        document.add(new Paragraph("\n"));

        float[] columnWidths = {200f, 100f, 100f};
        Table table = new Table(columnWidths);
        table.addHeaderCell("Descripción");
        table.addHeaderCell("Cantidad");
        table.addHeaderCell("Estado");

        if (datos.getDonaciones() != null) {
            for (Map<String, Object> d : datos.getDonaciones()) {
                table.addCell(d.get("descripcion") != null ? d.get("descripcion").toString() : "N/A");
                table.addCell(d.get("cantidad") != null ? d.get("cantidad").toString() : "0");
                table.addCell(d.get("estado") != null ? d.get("estado").toString() : "Pendiente");
            }
        }

        document.add(table);
        document.close();
        return out.toByteArray();
    }
}