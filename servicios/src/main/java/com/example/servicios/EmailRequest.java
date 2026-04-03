package com.example.servicios;

public class EmailRequest {
    private String destinatario;
    private String nombreFundacion;
    private String estado; // "PENDIENTE", "APROBADO", "RECHAZADO"

    // Getters y Setters
    public String getDestinatario() { return destinatario; }
    public void setDestinatario(String destinatario) { this.destinatario = destinatario; }
    public String getNombreFundacion() { return nombreFundacion; }
    public void setNombreFundacion(String nombreFundacion) { this.nombreFundacion = nombreFundacion; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }
}