package com.example.reportservice.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReportResponse {
    private String customerId;
    private String customerName;
    private String customerSegment;
    private LocalDate registrationDate;

    private Long totalSessions;
    private Long totalSessionDurationSeconds;
    private Double avgSessionDurationSeconds;
    private Long totalPageViews;
    private Long totalActions;
    private Double avgActionsPerSession;

    private LocalDate firstEventDate;
    private LocalDate lastEventDate;
    private Integer daysSinceLastEvent;

    private Double engagementScore;
    private String churnRisk;

    private LocalDate updatedAt;

}