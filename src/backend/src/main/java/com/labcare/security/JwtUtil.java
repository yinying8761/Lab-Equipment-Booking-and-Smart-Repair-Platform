package com.labcare.security;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 轻量 JWT（HS256）实现：仅使用 JDK 自带 HMAC，不引入额外依赖。
 * 载荷字段：sub=用户 id, u=用户名, n=显示名, r=角色, iat/exp=秒级时间戳。
 */
@Component
public class JwtUtil {

    private static final Base64.Encoder URL_ENCODER = Base64.getUrlEncoder().withoutPadding();
    private static final Base64.Decoder URL_DECODER = Base64.getUrlDecoder();
    private static final String HEADER = URL_ENCODER.encodeToString(
            "{\"alg\":\"HS256\",\"typ\":\"JWT\"}".getBytes(StandardCharsets.UTF_8));

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final byte[] secret;
    private final long expireSeconds;

    public JwtUtil(@Value("${labcare.jwt.secret}") String secret,
                   @Value("${labcare.jwt.expire-hours:12}") long expireHours) {
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
        this.expireSeconds = expireHours * 3600;
    }

    public String issue(CurrentUser user) {
        long now = Instant.now().getEpochSecond();
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("sub", String.valueOf(user.id()));
        payload.put("u", user.username());
        payload.put("n", user.displayName());
        payload.put("r", user.role());
        payload.put("iat", now);
        payload.put("exp", now + expireSeconds);
        try {
            String body = URL_ENCODER.encodeToString(objectMapper.writeValueAsBytes(payload));
            String signature = sign(HEADER + "." + body);
            return HEADER + "." + body + "." + signature;
        } catch (Exception e) {
            throw new IllegalStateException("签发令牌失败", e);
        }
    }

    /**
     * @return 解析成功返回用户，签名错误、过期或格式不合法返回 null
     */
    public CurrentUser parse(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        String[] parts = token.split("\\.");
        if (parts.length != 3) {
            return null;
        }
        String expected = sign(parts[0] + "." + parts[1]);
        if (!MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8),
                parts[2].getBytes(StandardCharsets.UTF_8))) {
            return null;
        }
        try {
            JsonNode node = objectMapper.readTree(URL_DECODER.decode(parts[1]));
            long exp = node.path("exp").asLong();
            if (exp < Instant.now().getEpochSecond()) {
                return null;
            }
            return new CurrentUser(
                    node.path("sub").asLong(),
                    node.path("u").asText(),
                    node.path("n").asText(),
                    node.path("r").asText());
        } catch (Exception e) {
            return null;
        }
    }

    private String sign(String content) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret, "HmacSHA256"));
            return URL_ENCODER.encodeToString(mac.doFinal(content.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("令牌签名失败", e);
        }
    }
}
