import { Card, Col, Row, Statistic } from 'antd';

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  suffix?: React.ReactNode;
}

export default function StatCard({ title, value, icon, color, suffix }: StatCardProps) {
  return (
    <Card className="stat-card" style={{ borderRadius: 8 }}>
      <Row align="middle" gutter={16}>
        <Col>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 12,
              background: `${color}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
              color,
            }}
          >
            {icon}
          </div>
        </Col>
        <Col flex={1}>
          <Statistic
            title={title}
            value={value}
            valueStyle={{ fontSize: 28, fontWeight: 600 }}
          />
          {suffix}
        </Col>
      </Row>
    </Card>
  );
}
