package com.example.servicios;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/email")
public class EmailController {

    // 2b. Reporte con PDF Adjunto para Donante
    @PostMapping("/enviar-reporte-donador")
    public ResponseEntity<String> enviarReporteDonador(@RequestBody EmailRequest request) {
        try {
            if (request.getDestinatario() == null || request.getDestinatario().isEmpty()) {
                return ResponseEntity.badRequest().body("{\"status\": \"Error\", \"error\": \"Sin destinatario\"}");
            }

            // Generamos el PDF usando el mismo servicio
            byte[] pdfContenido = pdfService.generarReporte(request);
            emailService.enviarReporteEmail(request, pdfContenido);

            return ResponseEntity.status(HttpStatus.OK)
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body("{\"status\": \"Reporte enviado con PDF\"}");

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}");
        }
    }

    @Autowired
    private EmailService emailService;

    @Autowired
    private PdfService pdfService;

    // 1. Notificaciones de cuenta (Pendiente/Aprobado)
    @PostMapping("/enviar")
    public ResponseEntity<String> enviarEmail(@RequestBody EmailRequest request) {
        try {
            emailService.enviarNotificacion(request);
            return ResponseEntity.ok("{\"status\": \"Notificación enviada\"}");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("{\"status\": \"Error\", \"error\": \"No se pudo enviar la notificación\"}");
        }
    }

    // 2. Reporte con PDF Adjunto
    @PostMapping("/enviar-reporte")
    public ResponseEntity<String> enviarReporte(@RequestBody EmailRequest request) {
        try {
            if (request.getDestinatario() == null || request.getDestinatario().isEmpty()) {
                return ResponseEntity.badRequest().body("{\"status\": \"Error\", \"error\": \"Sin destinatario\"}");
            }

            // Generamos el PDF usando el servicio que acabamos de pulir
            byte[] pdfContenido = pdfService.generarReporte(request);
            emailService.enviarReporteEmail(request, pdfContenido); 
            
            return ResponseEntity.status(HttpStatus.OK)
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body("{\"status\": \"Reporte enviado con PDF\"}");

        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}");
        }
    }

    // 3. Descarga directa (Para visualización inmediata en navegador)
    @GetMapping("/descargar-reporte")
    public ResponseEntity<byte[]> descargarReporte(
            @RequestParam int fundacion_id,
            @RequestParam String nombre,
            @RequestParam String nit,
            @RequestParam(required = false) String categoria,
            @RequestParam(name = "est", required = false) String estado) {
        System.out.println("[DEBUG] Filtro recibido - Categoria: " + categoria + ", Estado: " + estado);
        System.out.println("[DEBUG] fundacion_id recibido: " + fundacion_id);
        // Log para depuración del valor de estado
        System.out.println("[DEBUG] Valor recibido para estado: '" + estado + "'");
        try {
            // --- CONSULTA JDBC SEGURA ---
            java.util.List<java.util.Map<String, Object>> listaDonaciones = new java.util.ArrayList<>();
            int cantidad = 0;
            java.sql.Connection conn = null;
            java.sql.PreparedStatement stmt = null;
            java.sql.ResultSet rs = null;
            try {
                Class.forName("org.mariadb.jdbc.Driver");
                conn = java.sql.DriverManager.getConnection(
                    "jdbc:mariadb://localhost:3307/donaciones_db", "root", "");
                StringBuilder query = new StringBuilder();
                query.append("SELECT d.*, u.nombre as nombre_donante, c.nombre as nombre_categoria, df.estado as estado_fundacion ");
                query.append("FROM donaciones d ");
                query.append("JOIN usuarios u ON d.usuario_id = u.id ");
                query.append("LEFT JOIN categorias c ON d.categoria_id = c.id ");
                query.append("LEFT JOIN donaciones_fundaciones df ON d.id = df.donacion_id ");
                query.append("WHERE df.fundacion_id = ? ");
                java.util.List<Object> params = new java.util.ArrayList<>();
                params.add(fundacion_id);
                // Solo filtra por categoría si realmente hay filtro
                if (categoria != null && !categoria.trim().isEmpty() && !categoria.equalsIgnoreCase("Todas")) {
                    query.append(" AND c.nombre = ? ");
                    params.add(categoria);
                }
                // Filtro por estado_fundacion si se envía
                if (estado != null && !estado.trim().isEmpty() && !estado.equalsIgnoreCase("Todos")) {
                    query.append(" AND df.estado = ? ");
                    params.add(estado);
                }
                // Log para depuración de la consulta SQL y parámetros
                System.out.println("[DEBUG] Consulta SQL final: " + query.toString());
                System.out.println("[DEBUG] Parámetros: " + params);
                stmt = conn.prepareStatement(query.toString());
                for (int i = 0; i < params.size(); i++) {
                    stmt.setObject(i + 1, params.get(i));
                }
                rs = stmt.executeQuery();
                while (rs.next()) {
                    java.util.Map<String, Object> don = new java.util.HashMap<>();
                    don.put("id", rs.getObject("id"));
                    don.put("usuario_id", rs.getObject("usuario_id"));
                    don.put("categoria_id", rs.getObject("categoria_id"));
                    don.put("descripcion", rs.getString("descripcion") != null ? rs.getString("descripcion") : "");
                    don.put("cantidad", rs.getObject("cantidad") != null ? rs.getObject("cantidad") : 0);
                    don.put("estado", rs.getString("estado") != null ? rs.getString("estado") : "");
                    don.put("fecha", rs.getTimestamp("fecha"));
                    don.put("nombre_donante", rs.getString("nombre_donante") != null ? rs.getString("nombre_donante") : "");
                    don.put("nombre_categoria", rs.getString("nombre_categoria") != null ? rs.getString("nombre_categoria") : "");
                    don.put("estado_fundacion", rs.getString("estado_fundacion") != null ? rs.getString("estado_fundacion") : "");
                    listaDonaciones.add(don);
                }
                cantidad = listaDonaciones.size();
            } catch (Exception ex) {
                System.out.println("[ERROR] Consulta de donaciones: " + ex.getMessage());
            } finally {
                try { if (rs != null) rs.close(); } catch (Exception e) {}
                try { if (stmt != null) stmt.close(); } catch (Exception e) {}
                try { if (conn != null) conn.close(); } catch (Exception e) {}
            }

            EmailRequest datos = new EmailRequest();
            datos.setNombreFundacion(nombre);
            datos.setNit(nit);
            datos.setCantidadDonaciones(cantidad);
            datos.setCategoriaFiltrada(categoria);
            datos.setDonaciones(listaDonaciones);
            // Guardar el estado filtrado para referencia en el PDF si lo deseas
            datos.setEstadoFiltrado(estado);

            byte[] pdfBytes = pdfService.generarReporte(datos);
            System.out.println("[DEBUG] Bytes del PDF generado: " + pdfBytes.length);
            try {
                java.nio.file.Files.write(java.nio.file.Paths.get("reporte_test.pdf"), pdfBytes);
                System.out.println("[DEBUG] PDF guardado como reporte_test.pdf en el directorio del backend.");
            } catch (Exception ex) {
                System.out.println("[DEBUG] Error al guardar el PDF localmente: " + ex.getMessage());
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=Reporte_Red_Solidaria.pdf");

            return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
        } catch (Exception e) {
            System.out.println("[ERROR] Excepción al generar o enviar el PDF: " + e.getMessage());
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}