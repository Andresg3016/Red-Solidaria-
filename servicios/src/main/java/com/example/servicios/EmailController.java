package com.example.servicios;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/email")
public class EmailController {

    @Autowired
    private EmailService emailService;

    // IMPORTANTE: Inyectamos el servicio que genera el PDF
    @Autowired
    private PdfService pdfService;

    // 1. Endpoint original para notificaciones de cuenta (PENDIENTE/APROBADO)
    @PostMapping("/enviar")
    public String enviarEmail(@RequestBody EmailRequest request) {
        try {
            emailService.enviarNotificacion(request);
            return "{\"status\": \"Notificación enviada\"}";
        } catch (Exception e) {
            return "{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}";
        }
    }

    // 2. Endpoint específico para el Reporte con PDF Adjunto
    @PostMapping("/enviar-reporte")
    public String enviarReporte(@RequestBody EmailRequest request) {
        try {
            // A. Generamos el PDF en memoria primero
            byte[] pdfContenido = pdfService.generarReporte(request);
            
            // B. Enviamos el correo pasando los datos Y el PDF generado
            emailService.enviarReporteEmail(request, pdfContenido); 
            
            return "{\"status\": \"Reporte enviado con PDF\"}";
        } catch (Exception e) {
            return "{\"status\": \"Error\", \"error\": \"" + e.getMessage() + "\"}";
        }
    }
}