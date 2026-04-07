package com.example.servicios; 

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import jakarta.mail.internet.MimeMessage;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender mailSender;

    // --- MÉTODO 1: NOTIFICACIONES DE CUENTA (REGISTRO/APROBACIÓN) ---
    public void enviarNotificacion(EmailRequest request) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(request.getDestinatario());
            
            String subject = "";
            String mensajeCuerpo = "";
            String botonTexto = "Ir al Panel";
            
            String colorInicio = "#1e52ff"; 
            String colorFin = "#63ff5e";    
            String colorBoton = "#28a745";  

            switch (request.getEstado().toUpperCase()) {
                case "PENDIENTE":
                    subject = "Solicitud Recibida - Red Solidaria";
                    mensajeCuerpo = "Hemos recibido tu registro. Tu cuenta está en proceso de validación por nuestro equipo técnico.";
                    botonTexto = "Ver mi Estado";
                    break;
                case "APROBADO":
                    subject = "¡Felicidades! Tu cuenta ha sido activada";
                    mensajeCuerpo = "¡Buenas noticias! Tu cuenta ha sido activada con éxito. Ya puedes acceder al panel para gestionar donaciones.";
                    break;
                case "RECHAZADO":
                    subject = "Información sobre tu solicitud";
                    colorInicio = "#ff0000"; 
                    colorFin = "#dc2626";
                    colorBoton = "#b91c1c";
                    mensajeCuerpo = "Lamentamos informarte que tu solicitud no pudo ser aprobada en este momento.";
                    botonTexto = "Contactar Soporte";
                    break;
            }

            helper.setSubject(subject);

            String htmlContent = 
                "<div style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; padding: 20px;'>" +
                    "<div style='max-width: 600px; margin: auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.15); border: 1px solid #e1e1e1;'>" +
                        "<div style='background: linear-gradient(135deg, " + colorInicio + " 0%, " + colorFin + " 100%); padding: 40px; text-align: center; color: white;'>" +
                            "<img src='cid:logoImage' alt='Logo' style='max-height: 85px; background: white; padding: 10px; border-radius: 15px; margin-bottom: 15px;'/>" +
                            "<h1 style='margin: 0; font-size: 30px; font-weight: bold; text-shadow: 1px 1px 4px rgba(0,0,0,0.2);'>Red Solidaria</h1>" +
                        "</div>" +
                        "<div style='padding: 45px; text-align: center; background-color: #fffef5;'>" +
                            "<h2 style='color: #333; font-size: 24px; margin-bottom: 20px;'>¡Hola, " + request.getNombreFundacion() + "!</h2>" +
                            "<p style='color: #555; font-size: 17px; line-height: 1.6;'>" + mensajeCuerpo + "</p>" +
                            "<br><br>" +
                            "<a href='http://localhost:5000/login' style='background: linear-gradient(135deg, " + colorBoton + ", #20c997); color: white; padding: 16px 35px; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 16px; display: inline-block; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 5px 20px rgba(40, 167, 69, 0.3);'> " + botonTexto + " </a>" +
                        "</div>" +
                        "<div style='background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 13px; color: #777; border-top: 1px solid #eee;'>" +
                            "Estás recibiendo este correo porque formas parte de la <b>Red Solidaria</b>.<br>" +
                            "© 2026 Red Solidaria - Uniendo corazones." +
                        "</div>" +
                    "</div>" +
                "</div>";

            helper.setText(htmlContent, true);
            ClassPathResource image = new ClassPathResource("static/images/logo.jpeg");
            helper.addInline("logoImage", image);

            mailSender.send(message);
            System.out.println("✅ Notificación de estado enviada!");

        } catch (Exception e) {
            System.out.println("❌ Error: " + e.getMessage());
            e.printStackTrace(); 
        }
    }

    // --- MÉTODO 2: REPORTE MULTICRITERIO DE DONACIONES (SIN ARCHIVO ADJUNTO ABAJO) ---
    public void enviarReporteEmail(EmailRequest request, byte[] pdfContenido) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            // Mantenemos 'true' para permitir la imagen incrustada (Inline)
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(request.getDestinatario());
            helper.setSubject("Reporte de Actividad - " + request.getNombreFundacion());

            String colorInicio = "#1e52ff"; 
            String colorFin = "#63ff5e";    
            String colorBoton = "#28a745"; 

            // --- CONSTRUCCIÓN DE URL PARA EL BOTÓN DE DESCARGA ---
            String categoriaParaUrl = (request.getCategoriaFiltrada() != null && !request.getCategoriaFiltrada().isEmpty()) 
                                      ? request.getCategoriaFiltrada() : "Todas";
            
            String urlDescarga = "http://localhost:8080/api/email/descargar-reporte?" +
                                 "nombre=" + URLEncoder.encode(request.getNombreFundacion(), StandardCharsets.UTF_8) +
                                 "&nit=" + URLEncoder.encode(request.getNit(), StandardCharsets.UTF_8) +
                                 "&cantidad=" + request.getCantidadDonaciones() +
                                 "&categoria=" + URLEncoder.encode(categoriaParaUrl, StandardCharsets.UTF_8);

            String htmlContent = 
                "<div style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; padding: 20px;'>" +
                    "<div style='max-width: 600px; margin: auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.15); border: 1px solid #e1e1e1;'>" +
                        "<div style='background: linear-gradient(135deg, " + colorInicio + " 0%, " + colorFin + " 100%); padding: 40px; text-align: center; color: white;'>" +
                            "<img src='cid:logoImage' alt='Logo' style='max-height: 85px; background: white; padding: 10px; border-radius: 15px; margin-bottom: 15px;'/>" +
                            "<h1 style='margin: 0; font-size: 28px; font-weight: bold;'>Reporte de Donaciones</h1>" +
                            "<p style='margin-top: 10px; opacity: 0.9; font-size: 18px;'>" + request.getNombreFundacion() + "</p>" +
                        "</div>" +
                        "<div style='padding: 40px; text-align: center; background-color: #fffef5;'>" +
                            "<h2 style='color: #333;'>¡Hola, " + request.getNombreFundacion() + "!</h2>" +
                            "<p style='color: #555; font-size: 16px;'>Hemos generado el reporte detallado que solicitaste con el logo de <b>Red Solidaria</b>.</p>" +
                            "<div style='background: #f8f9fa; border-radius: 15px; padding: 25px; margin: 25px 0; text-align: left; border: 1px dashed #ccc;'>" +
                                "<p style='margin: 5px 0;'><b>Identificación (NIT):</b> " + request.getNit() + "</p>" +
                                "<p style='margin: 5px 0;'><b>Filtro Categoría:</b> " + categoriaParaUrl + "</p>" +
                                "<div style='margin-top: 15px; padding-top: 15px; border-top: 2px solid " + colorFin + ";'>" +
                                    "<p style='font-size: 20px; margin: 0;'><b>Total Donaciones Encontradas:</b> <span style='color: " + colorInicio + "; font-weight: 800;'>" + request.getCantidadDonaciones() + "</span></p>" +
                                "</div>" +
                            "</div>" +
                            "<p style='color: #777; font-size: 14px;'>Puedes descargar el reporte PDF directamente usando el botón de abajo.</p>" +
                            "<br>" +
                            "<a href='" + urlDescarga + "' style='background: linear-gradient(135deg, " + colorBoton + ", #20c997); color: white; padding: 16px 35px; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 16px; display: inline-block; text-transform: uppercase; box-shadow: 0 5px 20px rgba(40, 167, 69, 0.3);'> DESCARGAR REPORTE PDF </a>" +
                        "</div>" +
                        "<div style='background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 13px; color: #777; border-top: 1px solid #eee;'>" +
                            "Este es un reporte automático generado por el sistema <b>Red Solidaria</b>.<br>" +
                            "© 2026 Red Solidaria - Uniendo corazones." +
                        "</div>" +
                    "</div>" +
                "</div>";

            helper.setText(htmlContent, true);

            ClassPathResource image = new ClassPathResource("static/images/logo.jpeg");
            helper.addInline("logoImage", image);

            // SECCIÓN ELIMINADA: Ya no se llama a helper.addAttachment(...)

            mailSender.send(message);
            System.out.println("✅ Reporte enviado exitosamente (Sin archivo adjunto físico)");

        } catch (Exception e) {
            System.out.println("❌ Error enviando reporte: " + e.getMessage());
            e.printStackTrace();
        }
    }
}