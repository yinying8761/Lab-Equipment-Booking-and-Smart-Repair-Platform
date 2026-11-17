package com.labcare.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.labcare.common.BusinessException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.Map;

/**
 * 与 Python/LangChain AI 服务通信的客户端。
 * AI 服务不可用时抛出 503，业务系统（设备、预约、手动报修）不受影响。
 */
@Component
public class AiClient {

    private static final Logger log = LoggerFactory.getLogger(AiClient.class);

    private final RestClient restClient;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final String internalToken;

    public AiClient(@Value("${labcare.ai.base-url}") String baseUrl,
                    @Value("${labcare.ai.connect-timeout-seconds:5}") int connectTimeout,
                    @Value("${labcare.ai.read-timeout-seconds:90}") int readTimeout,
                    @Value("${labcare.ai.internal-token:}") String internalToken) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(connectTimeout));
        factory.setReadTimeout(Duration.ofSeconds(readTimeout));
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(factory)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();
        this.internalToken = internalToken;
    }

    public boolean healthy() {
        try {
            JsonNode node = restClient.get().uri("/health").retrieve().body(JsonNode.class);
            return node != null && "ok".equals(node.path("status").asText());
        } catch (Exception e) {
            return false;
        }
    }

    public JsonNode post(String path, Object body) {
        try {
            return restClient.post().uri(path).body(body).retrieve().body(JsonNode.class);
        } catch (Exception e) {
            log.warn("调用 AI 服务失败 {}: {}", path, e.getMessage());
            throw new BusinessException(503, "AI 服务暂不可用，请稍后重试或使用手动报修");
        }
    }

    public String getInternalToken() {
        return internalToken;
    }

    public ObjectMapper mapper() {
        return objectMapper;
    }

    public Map<String, Object> body(Object... keyValues) {
        Map<String, Object> map = new java.util.LinkedHashMap<>();
        for (int i = 0; i + 1 < keyValues.length; i += 2) {
            map.put(String.valueOf(keyValues[i]), keyValues[i + 1]);
        }
        return map;
    }
}
