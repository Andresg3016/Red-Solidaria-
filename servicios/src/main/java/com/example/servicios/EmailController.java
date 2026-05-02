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

    @Autowired
    private EmailService emailService;

    @Autowired
    private PdfService pdfService;

    // 1. Notificaciones de cuenta (Pendiente/Aprobado/Rechazado)
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

    // 2. Reporte fundación con PDF adjunto + botón descarga
    @PostMapping("/enviar-reporte")
    public ResponseEntity<String> enviarReporte(@RequestBody EmailRequest request) {
        try {
            if (request.getDestinatario() == null || request.getDestinatario().isEmpty()) {
                return ResponseEntity.badRequest()
                    .body("{\"status\": \"Error\", \"error\": \"Sin destinatario\"}");
            }
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

    // 2b. Reporte con PDF Adjunto para Donante
    @PostMapping("/enviar-reporte-donador")
    public ResponseEntity<String> enviarReporteDonador(@RequestBody EmailRequest request) {
        try {
            if (request.getDestinatario() == null || request.getDestinatario().isEmpty()) {
                return ResponseEntity.badRequest()
                    .body("{\"status\": \"Error\", \"error\": \"Sin destinatario\"}");
            }
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

    // 3. Descarga directa para fundación (con fundacion_id)
    @GetMapping("/descargar-reporte")
    public ResponseEntity<byte[]> descargarReporte(
            @RequestParam int fundacion_id,
            @RequestParam String nombre,
            @RequestParam String nit,
            @RequestParam(required = false) String categoria,
            @RequestParam(name = "est", required = false) String estado) {

        System.out.println("[DEBUG] descargar-reporte - fundacion_id: " + fundacion_id
            + " categoria: " + categoria + " estado: " + estado);
        try {
            List<Map<String, Object>> listaDonaciones = new ArrayList<>();
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
                List<Object> params = new ArrayList<>();
                params.add(fundacion_id);
                if (categoria != null && !categoria.trim().isEmpty() && !categoria.equalsIgnoreCase("Todas")) {
                    query.append("AND c.nombre = ? ");
                    params.add(categoria);
                }
                if (estado != null && !estado.trim().isEmpty() && !estado.equalsIgnoreCase("Todos")) {
                    query.append("AND df.estado = ? ");
                    params.add(estado);
                }
                stmt = conn.prepareStatement(query.toString());
                for (int i = 0; i < params.size(); i++) stmt.setObject(i + 1, params.get(i));
                rs = stmt.executeQuery();
                while (rs.next()) {
                    Map<String, Object> don = new HashMap<>();
                    don.put("descripcion",      rs.getString("descripcion") != null ? rs.getString("descripcion") : "");
                    don.put("cantidad",          rs.getObject("cantidad") != null ? rs.getObject("cantidad") : 0);
                    don.put("estado",            rs.getString("estado") != null ? rs.getString("estado") : "");
                    don.put("estado_fundacion",  rs.getString("estado_fundacion") != null ? rs.getString("estado_fundacion") : "");
                    don.put("nombre_donante",    rs.getString("nombre_donante") != null ? rs.getString("nombre_donante") : "");
                    don.put("nombre_categoria",  rs.getString("nombre_categoria") != null ? rs.getString("nombre_categoria") : "");
                    listaDonaciones.add(don);
                }
            } finally {
                try { if (rs != null) rs.close(); } catch (Exception e) {}
                try { if (stmt != null) stmt.close(); } catch (Exception e) {}
                try { if (conn != null) conn.close(); } catch (Exception e) {}
            }

            EmailRequest datos = new EmailRequest();
            datos.setNombreFundacion(nombre);
            datos.setNit(nit);
            datos.setCantidadDonaciones(listaDonaciones.size());
            datos.setCategoriaFiltrada(categoria);
            datos.setEstadoFiltrado(estado);
            datos.setDonaciones(listaDonaciones);

            byte[] pdfBytes = pdfService.generarReporte(datos);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=Reporte_Red_Solidaria.pdf");
            return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);

        } catch (Exception e) {
            System.out.println("[ERROR] descargar-reporte: " + e.getMessage());
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // ══════════════════════════════════════════════════════════════
    // 4. DESCARGA REPORTE ADMIN — 3 secciones: Donaciones,
    //    Fundaciones y Donantes, con filtros multicriterio.
    // ══════════════════════════════════════════════════════════════
    @GetMapping("/descargar-reporte-admin")
    public ResponseEntity<byte[]> descargarReporteAdmin(
            @RequestParam(required = false) String nombre,
            @RequestParam(required = false) String categoria,
            @RequestParam(name = "est", required = false) String estado,
            @RequestParam(required = false) String donante,
            @RequestParam(required = false) String fundacion) {

        System.out.println("[DEBUG] descargar-reporte-admin - categoria: " + categoria
            + " estado: " + estado + " donante: " + donante + " fundacion: " + fundacion);
        try {
            List<Map<String, Object>> listaDonaciones  = new ArrayList<>();
            List<Map<String, Object>> listaFundaciones = new ArrayList<>();
            List<Map<String, Object>> listaDonantes    = new ArrayList<>();

            java.sql.Connection conn = null;
            try {
                Class.forName("org.mariadb.jdbc.Driver");
                conn = java.sql.DriverManager.getConnection(
                    "jdbc:mariadb://localhost:3307/donaciones_db", "root", "");

                // ── CONSULTA 1: DONACIONES ──
                StringBuilder qDon = new StringBuilder();
                qDon.append("SELECT d.descripcion, d.cantidad, u.nombre AS nombre_donante, ");
                qDon.append("c.nombre AS nombre_categoria, f.nombre AS fundacion_nombre, ");
                qDon.append("COALESCE(df.estado, d.estado) AS estado_fundacion ");
                qDon.append("FROM donaciones d ");
                qDon.append("INNER JOIN usuarios u ON d.usuario_id = u.id ");
                qDon.append("LEFT JOIN categorias c ON d.categoria_id = c.id ");
                qDon.append("LEFT JOIN donaciones_fundaciones df ON d.id = df.donacion_id ");
                qDon.append("LEFT JOIN fundaciones fun ON df.fundacion_id = fun.id ");
                qDon.append("LEFT JOIN usuarios f ON fun.usuario_id = f.id ");
                qDon.append("WHERE 1=1 ");
                List<Object> pDon = new ArrayList<>();
                if (categoria != null && !categoria.trim().isEmpty() && !categoria.equalsIgnoreCase("Todas")) {
                    qDon.append("AND c.nombre = ? ");
                    pDon.add(categoria);
                }
                if (estado != null && !estado.trim().isEmpty() && !estado.equalsIgnoreCase("Todos")) {
                    qDon.append("AND COALESCE(df.estado, d.estado) = ? ");
                    pDon.add(estado);
                }
                if (donante != null && !donante.trim().isEmpty()) {
                    qDon.append("AND u.nombre LIKE ? ");
                    pDon.add("%" + donante + "%");
                }
                if (fundacion != null && !fundacion.trim().isEmpty()) {
                    qDon.append("AND f.nombre LIKE ? ");
                    pDon.add("%" + fundacion + "%");
                }
                qDon.append("ORDER BY d.fecha DESC");

                java.sql.PreparedStatement stmtDon = conn.prepareStatement(qDon.toString());
                for (int i = 0; i < pDon.size(); i++) stmtDon.setObject(i + 1, pDon.get(i));
                java.sql.ResultSet rsDon = stmtDon.executeQuery();
                while (rsDon.next()) {
                    Map<String, Object> row = new HashMap<>();
                    row.put("descripcion",      rsDon.getString("descripcion") != null ? rsDon.getString("descripcion") : "");
                    row.put("cantidad",          rsDon.getObject("cantidad") != null ? rsDon.getObject("cantidad") : 0);
                    row.put("estado_fundacion",  rsDon.getString("estado_fundacion") != null ? rsDon.getString("estado_fundacion") : "");
                    row.put("estado",            rsDon.getString("estado_fundacion") != null ? rsDon.getString("estado_fundacion") : "");
                    row.put("nombre_donante",    rsDon.getString("nombre_donante") != null ? rsDon.getString("nombre_donante") : "");
                    row.put("nombre_categoria",  rsDon.getString("nombre_categoria") != null ? rsDon.getString("nombre_categoria") : "");
                    row.put("fundacion_nombre",  rsDon.getString("fundacion_nombre") != null ? rsDon.getString("fundacion_nombre") : "");
                    listaDonaciones.add(row);
                }
                rsDon.close(); stmtDon.close();

                // ── CONSULTA 2: FUNDACIONES ──
                StringBuilder qFun = new StringBuilder();
                qFun.append("SELECT f.nombre, f.nit, u.correo, u.fecha_registro, f.estado_validacion ");
                qFun.append("FROM fundaciones f ");
                qFun.append("INNER JOIN usuarios u ON f.usuario_id = u.id ");
                qFun.append("WHERE 1=1 ");
                List<Object> pFun = new ArrayList<>();
                if (fundacion != null && !fundacion.trim().isEmpty()) {
                    qFun.append("AND f.nombre LIKE ? ");
                    pFun.add("%" + fundacion + "%");
                }
                if (estado != null && !estado.trim().isEmpty() && !estado.equalsIgnoreCase("Todos")) {
                    qFun.append("AND f.estado_validacion = ? ");
                    pFun.add(estado);
                }
                qFun.append("ORDER BY u.fecha_registro DESC");

                java.sql.PreparedStatement stmtFun = conn.prepareStatement(qFun.toString());
                for (int i = 0; i < pFun.size(); i++) stmtFun.setObject(i + 1, pFun.get(i));
                java.sql.ResultSet rsFun = stmtFun.executeQuery();
                while (rsFun.next()) {
                    Map<String, Object> row = new HashMap<>();
                    row.put("nombre",             rsFun.getString("nombre") != null ? rsFun.getString("nombre") : "");
                    row.put("nit",                rsFun.getString("nit") != null ? rsFun.getString("nit") : "");
                    row.put("correo",             rsFun.getString("correo") != null ? rsFun.getString("correo") : "");
                    row.put("fecha_registro",     rsFun.getString("fecha_registro") != null ? rsFun.getString("fecha_registro") : "");
                    row.put("estado_validacion",  rsFun.getString("estado_validacion") != null ? rsFun.getString("estado_validacion") : "");
                    listaFundaciones.add(row);
                }
                rsFun.close(); stmtFun.close();

                // ── CONSULTA 3: DONANTES ──
                StringBuilder qDonan = new StringBuilder();
                qDonan.append("SELECT nombre, correo, fecha_registro, estado ");
                qDonan.append("FROM usuarios WHERE rol_id = 2 ");
                List<Object> pDonan = new ArrayList<>();
                if (donante != null && !donante.trim().isEmpty()) {
                    qDonan.append("AND nombre LIKE ? ");
                    pDonan.add("%" + donante + "%");
                }
                if (estado != null && !estado.trim().isEmpty() && !estado.equalsIgnoreCase("Todos")) {
                    qDonan.append("AND estado = ? ");
                    pDonan.add(estado);
                }
                qDonan.append("ORDER BY fecha_registro DESC");

                java.sql.PreparedStatement stmtDonan = conn.prepareStatement(qDonan.toString());
                for (int i = 0; i < pDonan.size(); i++) stmtDonan.setObject(i + 1, pDonan.get(i));
                java.sql.ResultSet rsDonan = stmtDonan.executeQuery();
                while (rsDonan.next()) {
                    Map<String, Object> row = new HashMap<>();
                    row.put("nombre",          rsDonan.getString("nombre") != null ? rsDonan.getString("nombre") : "");
                    row.put("correo",          rsDonan.getString("correo") != null ? rsDonan.getString("correo") : "");
                    row.put("fecha_registro",  rsDonan.getString("fecha_registro") != null ? rsDonan.getString("fecha_registro") : "");
                    row.put("estado",          rsDonan.getString("estado") != null ? rsDonan.getString("estado") : "");
                    listaDonantes.add(row);
                }
                rsDonan.close(); stmtDonan.close();

            } finally {
                try { if (conn != null) conn.close(); } catch (Exception e) {}
            }

            // Armar el EmailRequest con las 3 listas
            EmailRequest datos = new EmailRequest();
            datos.setNombreFundacion(nombre != null ? nombre : "Administrador - Red Solidaria");
            datos.setNit("Panel Administrativo");
            datos.setCantidadDonaciones(listaDonaciones.size());
            datos.setCategoriaFiltrada(categoria);
            datos.setEstadoFiltrado(estado);
            datos.setDonaciones(listaDonaciones);
            datos.setFundaciones(listaFundaciones);
            datos.setDonantes(listaDonantes);

            byte[] pdfBytes = pdfService.generarReporteAdmin(datos);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=Reporte_Admin_Red_Solidaria.pdf");
            return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);

        } catch (Exception e) {
            System.out.println("[ERROR] descargar-reporte-admin: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}