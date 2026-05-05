package com.example.reportservice.repository;

import com.example.reportservice.model.ReportResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;
import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

@Slf4j
@Repository
@RequiredArgsConstructor
public class ClickHouseRepository {

    private final DataSource dataSource;

    public ReportResponse getCustomerReport(String customerId) {
        String sql = """
            SELECT 
                customer_id,
                customer_name,
                customer_segment,
                registration_date,
                total_sessions,
                total_session_duration_seconds,
                avg_session_duration_seconds,
                total_page_views,
                total_actions,
                avg_actions_per_session,
                first_event_date,
                last_event_date,
                days_since_last_event,
                engagement_score,
                churn_risk,
                updated_at
            FROM customer_telemetry_mart
            WHERE customer_name = ?
            """;

        try (Connection conn = dataSource.getConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {

            stmt.setString(1, customerId);
            ResultSet rs = stmt.executeQuery();

            if (rs.next()) {
                return ReportResponse.builder()
                        .customerId(rs.getString("customer_id"))
                        .customerName(rs.getString("customer_name"))
                        .customerSegment(rs.getString("customer_segment"))
                        .registrationDate(rs.getDate("registration_date") != null ?
                                rs.getDate("registration_date").toLocalDate() : null)
                        .totalSessions(rs.getLong("total_sessions"))
                        .totalSessionDurationSeconds(rs.getLong("total_session_duration_seconds"))
                        .avgSessionDurationSeconds(rs.getDouble("avg_session_duration_seconds"))
                        .totalPageViews(rs.getLong("total_page_views"))
                        .totalActions(rs.getLong("total_actions"))
                        .avgActionsPerSession(rs.getDouble("avg_actions_per_session"))
                        .firstEventDate(rs.getDate("first_event_date") != null ?
                                rs.getDate("first_event_date").toLocalDate() : null)
                        .lastEventDate(rs.getDate("last_event_date") != null ?
                                rs.getDate("last_event_date").toLocalDate() : null)
                        .daysSinceLastEvent(rs.getInt("days_since_last_event"))
                        .engagementScore(rs.getDouble("engagement_score"))
                        .churnRisk(rs.getString("churn_risk"))
                        .updatedAt(rs.getDate("updated_at") != null ?
                                rs.getDate("updated_at").toLocalDate() : null)
                        .build();
            }

        } catch (Exception e) {
            log.error("Error fetching report for customer {}", customerId, e);
            throw new RuntimeException("Failed to fetch report", e);
        }

        return null;
    }
}