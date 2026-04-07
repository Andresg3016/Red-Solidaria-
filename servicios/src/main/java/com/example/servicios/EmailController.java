package com.example.servicios;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

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

    // 1. Notificaciones de cuenta (Pendiente/Aprobado)
    @PostMapping("/enviar")
    public ResponseEntity<String> enviarEmail(@RequestBody EmailRequest request) {
        try {
            emailService.enviarNotificacion(request);
            return ResponseEntity.ok("{\"status\": \"Notificación enviada\"}");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}");
        }
    }

    // 2. Reporte con PDF Adjunto (CORRECCIÓN PARA EVITAR DUPLICADOS)
    @PostMapping("/enviar-reporte")
    public ResponseEntity<String> enviarReporte(@RequestBody EmailRequest request) {
        try {
            if (request.getDestinatario() == null || request.getDestinatario().isEmpty()) {
                return ResponseEntity.badRequest().body("{\"status\": \"Error\", \"error\": \"Sin destinatario\"}");
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

    // 3. Descarga directa (CORREGIDO PARA MOSTRAR DATOS EN LA TABLA)
    @GetMapping("/descargar-reporte")
    public ResponseEntity<byte[]> descargarReporte(
            @RequestParam String nombre,
            @RequestParam String nit,
            @RequestParam int cantidad,
            @RequestParam(required = false) String categoria) {
        
        try {
            EmailRequest datos = new EmailRequest();
            datos.setNombreFundacion(nombre);
            datos.setNit(nit);
            datos.setCantidadDonaciones(cantidad);
            datos.setCategoriaFiltrada(categoria);

            // --- SOLUCIÓN: Si no hay lista, creamos una fila de resumen para que la tabla no salga vacía ---
            List<Map<String, Object>> listaDonaciones = new ArrayList<>();
            Map<String, Object> filaResumen = new HashMap<>();
            filaResumen.put("descripcion", "Donaciones filtradas: " + (categoria != null ? categoria : "Todas"));
            filaResumen.put("cantidad", cantidad);
            filaResumen.put("estado", "Verificado");
            listaDonaciones.add(filaResumen);
            
            datos.setDonaciones(listaDonaciones); // Ahora la tabla sí tendrá qué mostrar

            byte[] pdfBytes = pdfService.generarReporte(datos);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.add(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=Reporte_Red_Solidaria.pdf");

            return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
            
        } catch (Exception e) {
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}