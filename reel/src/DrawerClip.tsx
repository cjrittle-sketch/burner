import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont as loadDisplay} from '@remotion/google-fonts/BricolageGrotesque';
import {loadFont as loadBody} from '@remotion/google-fonts/AtkinsonHyperlegibleNext';
import {loadFont as loadMono} from '@remotion/google-fonts/MartianMono';

const display = loadDisplay('normal', {weights: ['700', '800'], subsets: ['latin']}).fontFamily;
const body = loadBody('normal', {weights: ['400', '600', '700'], subsets: ['latin']}).fontFamily;
const mono = loadMono('normal', {weights: ['400', '600'], subsets: ['latin']}).fontFamily;

// Brand tokens (brand/system.html)
const C = {
  handset: '#1B1D22',
  surface: '#23262D',
  line: '#30343D',
  graphite: '#4A505C',
  wire: '#9AA0AD',
  lcd: '#E6E8EC',
  ash: '#F4F5F8',
  burn: '#FF6A13',
  burnSoft: '#FF8A4C',
  fuse: '#8C9BFF',
  tether: '#3FB7A6',
};

// Timeline, in frames at 30 fps
const INTRO = 105;
const MAIN = 480;
const END = 150;
export const DURATION = INTRO + MAIN + END;

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const fadeInOut = (frame: number, total: number, inLen = 12, outLen = 15) =>
  interpolate(frame, [0, inLen, total - outLen, total], [0, 1, 1, 0], clamp);

/* ---------------------------------------------------------------- phone */

const PhoneShell: React.FC<{
  width: number;
  glow: number;
  children?: React.ReactNode;
}> = ({width, glow, children}) => {
  const height = width * 2.05;
  return (
    <div
      style={{
        width,
        height,
        borderRadius: width * 0.13,
        background: C.handset,
        border: `${width * 0.03}px solid ${C.graphite}`,
        boxShadow: `0 0 ${80 * glow}px ${20 * glow}px rgba(255,106,19,${0.28 * glow})`,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: width * 0.035,
          left: '50%',
          width: width * 0.04,
          height: width * 0.04,
          marginLeft: -width * 0.02,
          borderRadius: '50%',
          background: '#000',
          zIndex: 5,
        }}
      />
      {children}
    </div>
  );
};

const APPS = [
  {name: 'Photos', color: '#4A505C'},
  {name: 'Maps', color: '#4A505C'},
  {name: 'Tinder', color: '#4A505C'},
  {name: 'Vinted', color: C.burn},
  {name: 'Snapchat', color: '#4A505C'},
  {name: 'Uber Eats', color: '#4A505C'},
  {name: 'Ring', color: '#4A505C'},
  {name: 'Amazon', color: '#4A505C'},
  {name: 'Airbnb', color: '#4A505C'},
];

const HomeScreen: React.FC<{tap: number}> = ({tap}) => (
  <AbsoluteFill style={{padding: '70px 26px', background: '#2A2E36'}}>
    <div
      style={{
        fontFamily: display,
        fontWeight: 800,
        fontSize: 64,
        color: C.lcd,
        textAlign: 'center',
        marginBottom: 60,
      }}
    >
      9:41
    </div>
    <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', rowGap: 34}}>
      {APPS.map((a) => {
        const isTarget = a.name === 'Vinted';
        return (
          <div key={a.name} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, position: 'relative'}}>
            <div
              style={{
                width: 66,
                height: 66,
                borderRadius: 18,
                background: a.color,
                transform: isTarget ? `scale(${1 - 0.12 * Math.sin(Math.PI * tap)})` : undefined,
              }}
            />
            {isTarget && tap > 0 && tap < 1 ? (
              <div
                style={{
                  position: 'absolute',
                  top: 33 - 50 * tap,
                  left: '50%',
                  marginLeft: -50 * tap,
                  width: 100 * tap,
                  height: 100 * tap,
                  borderRadius: '50%',
                  border: `3px solid ${C.ash}`,
                  opacity: 1 - tap,
                }}
              />
            ) : null}
            <div style={{fontFamily: body, fontSize: 15, color: C.lcd}}>{a.name}</div>
          </div>
        );
      })}
    </div>
  </AbsoluteFill>
);

const Listing: React.FC<{title: string; price: string; status: React.ReactNode}> = ({title, price, status}) => (
  <div
    style={{
      display: 'flex',
      gap: 14,
      alignItems: 'center',
      padding: 12,
      borderRadius: 16,
      background: C.surface,
      border: `1px solid ${C.line}`,
    }}
  >
    <div style={{width: 64, height: 64, flexShrink: 0, borderRadius: 10, background: C.graphite}} />
    <div style={{flex: 1, display: 'grid', gap: 6}}>
      <div style={{fontFamily: body, fontWeight: 700, fontSize: 19, color: C.lcd, whiteSpace: 'nowrap'}}>{title}</div>
      <div style={{fontFamily: mono, fontSize: 16, color: C.wire}}>{price}</div>
    </div>
    {status}
  </div>
);

const Chip: React.FC<{label: string; color: string; scale?: number}> = ({label, color, scale = 1}) => (
  <div
    style={{
      fontFamily: mono,
      fontWeight: 600,
      fontSize: 12,
      letterSpacing: 1,
      textTransform: 'uppercase',
      padding: '5px 8px',
      borderRadius: 99,
      border: `2px solid ${color}`,
      color,
      transform: `scale(${scale})`,
    }}
  >
    {label}
  </div>
);

const ListingsScreen: React.FC<{sold: number}> = ({sold}) => (
  <AbsoluteFill style={{padding: '64px 20px', background: C.handset, display: 'flex', flexDirection: 'column', gap: 16}}>
    <div style={{fontFamily: display, fontWeight: 800, fontSize: 34, color: C.lcd, marginBottom: 8}}>Your listings</div>
    <Listing
      title="Denim jacket"
      price="€25"
      status={
        sold > 0 ? (
          <Chip label="Sold" color={C.tether} scale={0.6 + 0.4 * sold} />
        ) : (
          <Chip label="Active" color={C.wire} />
        )
      }
    />
    <Listing title="Desk lamp" price="€15" status={<Chip label="Active" color={C.wire} />} />
    <Listing title="Sneakers" price="€40" status={<Chip label="Active" color={C.wire} />} />
  </AbsoluteFill>
);

/* ---------------------------------------------------------------- chat */

const Bubble: React.FC<{
  from: 'user' | 'muse';
  children: React.ReactNode;
  enter: number;
}> = ({from, children, enter}) => {
  const isUser = from === 'user';
  return (
    <div
      style={{
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        maxWidth: '88%',
        padding: '16px 20px',
        borderRadius: 22,
        borderBottomRightRadius: isUser ? 6 : 22,
        borderBottomLeftRadius: isUser ? 22 : 6,
        background: isUser ? C.lcd : C.surface,
        color: isUser ? C.handset : C.lcd,
        border: isUser ? 'none' : `1px solid ${C.line}`,
        fontFamily: body,
        fontSize: 27,
        lineHeight: 1.3,
        opacity: enter,
        transform: `translateY(${(1 - enter) * 24}px)`,
      }}
    >
      {children}
    </div>
  );
};

type Step = {label: string; start: number; done: number};

const StepRow: React.FC<{step: Step; frame: number}> = ({step, frame}) => {
  const show = interpolate(frame, [step.start, step.start + 8], [0, 1], clamp);
  const isDone = frame >= step.done;
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 12, opacity: show}}>
      <div
        style={{
          width: 12,
          height: 12,
          borderRadius: '50%',
          background: isDone ? C.tether : C.fuse,
          opacity: isDone ? 1 : 0.55 + 0.45 * Math.abs(Math.sin(frame / 6)),
        }}
      />
      <div style={{fontFamily: body, fontSize: 22, color: isDone ? C.lcd : C.wire}}>
        {step.label}
        {isDone ? ' ✓' : '…'}
      </div>
    </div>
  );
};

const BurnerCard: React.FC<{frame: number; steps: Step[]; enter: number}> = ({frame, steps, enter}) => (
  <div
    style={{
      alignSelf: 'flex-start',
      width: '88%',
      padding: '14px 18px',
      borderRadius: 14,
      background: C.handset,
      border: `1px solid ${C.line}`,
      display: 'grid',
      gap: 10,
      opacity: enter,
      transform: `translateY(${(1 - enter) * 24}px)`,
    }}
  >
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontFamily: mono,
        fontSize: 14,
        letterSpacing: 1.5,
        color: C.burnSoft,
        borderBottom: `1px solid ${C.line}`,
        paddingBottom: 8,
      }}
    >
      <span>&gt;_ burner</span>
      <span style={{color: C.wire, textTransform: 'uppercase'}}>your spare phone</span>
    </div>
    {steps.map((s) => (
      <StepRow key={s.label} step={s} frame={frame} />
    ))}
  </div>
);

/* ---------------------------------------------------------------- scenes */

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const l1 = spring({frame, fps, config: {damping: 200}});
  const l2 = spring({frame: frame - 18, fps, config: {damping: 200}});
  const phone = spring({frame: frame - 30, fps, config: {damping: 20, stiffness: 120}});
  const opacity = fadeInOut(frame, INTRO, 1);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 50, opacity}}>
      <div style={{textAlign: 'center', fontFamily: display, fontWeight: 800, color: C.ash, fontSize: 96, lineHeight: 1}}>
        <div style={{opacity: l1, transform: `translateY(${(1 - l1) * 30}px)`}}>Your old phone</div>
        <div style={{opacity: l2, transform: `translateY(${(1 - l2) * 30}px)`, color: C.burn}}>has a new job.</div>
      </div>
      <div style={{position: 'relative', transform: `translateY(${(1 - phone) * 160}px)`, opacity: phone}}>
        <PhoneShell width={170} glow={0}>
          <AbsoluteFill style={{background: '#14161A'}} />
        </PhoneShell>
        {/* the drawer it lives in */}
        <div
          style={{
            position: 'absolute',
            left: -170,
            right: -170,
            bottom: -18,
            height: 130,
            borderRadius: 18,
            border: `6px solid ${C.graphite}`,
            background: C.surface,
          }}
        >
          <div style={{position: 'absolute', left: '50%', top: 52, width: 120, height: 14, marginLeft: -60, borderRadius: 7, background: C.graphite}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const USER_TEXT = 'Use my burner to see if my Vinted listing sold.';

const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // chat timings (local frames)
  const userIn = spring({frame: frame - 10, fps, config: {damping: 200}});
  const typed = Math.round(interpolate(frame, [12, 75], [0, USER_TEXT.length], clamp));
  const cardIn = spring({frame: frame - 95, fps, config: {damping: 200}});
  const steps: Step[] = [
    {label: 'Waking the phone', start: 100, done: 135},
    {label: 'Opening Vinted', start: 140, done: 185},
    {label: 'Checking your listings', start: 190, done: 265},
  ];
  const replyIn = spring({frame: frame - 285, fps, config: {damping: 200}});
  const noteIn = spring({frame: frame - 320, fps, config: {damping: 200}});
  const captionIn = spring({frame: frame - 380, fps, config: {damping: 200}});

  // phone timings
  const screenOn = interpolate(frame, [105, 120], [0, 1], clamp);
  const tap = interpolate(frame, [150, 168], [0, 1], clamp);
  const showListings = frame >= 172;
  const listingsIn = interpolate(frame, [172, 184], [0, 1], {...clamp, easing: Easing.out(Easing.quad)});
  const sold = spring({frame: frame - 255, fps, config: {damping: 12, stiffness: 160}});
  const glow = screenOn * (frame < 265 ? 1 : interpolate(frame, [265, 320], [1, 0.4], clamp));

  const opacity = fadeInOut(frame, MAIN);

  return (
    <AbsoluteFill style={{opacity}}>
      {/* chat with the AI assistant */}
      <div
        style={{
          position: 'absolute',
          left: 56,
          top: 70,
          width: 560,
          height: 760,
          display: 'flex',
          flexDirection: 'column',
          gap: 22,
        }}
      >
        <div style={{fontFamily: mono, fontSize: 18, letterSpacing: 2, textTransform: 'uppercase', color: C.wire}}>
          You → Muse
        </div>
        <Bubble from="user" enter={userIn}>
          {USER_TEXT.slice(0, typed)}
          {typed < USER_TEXT.length ? <span style={{opacity: 0.4}}>|</span> : null}
        </Bubble>
        {frame >= 95 ? <BurnerCard frame={frame} steps={steps} enter={cardIn} /> : null}
        {frame >= 285 ? (
          <Bubble from="muse" enter={replyIn}>
            Yes! Your denim jacket sold for €25.
          </Bubble>
        ) : null}
        {frame >= 320 ? (
          <div style={{fontFamily: body, fontSize: 20, color: C.wire, opacity: noteIn, paddingLeft: 6}}>
            It only looked. Nothing gets sent, posted or bought without your yes.
          </div>
        ) : null}
      </div>

      {/* the phone in the drawer */}
      <div style={{position: 'absolute', left: 680, top: 110}}>
        <PhoneShell width={340} glow={glow}>
          <AbsoluteFill style={{opacity: screenOn}}>
            {showListings ? (
              <AbsoluteFill style={{opacity: listingsIn}}>
                <ListingsScreen sold={frame >= 255 ? sold : 0} />
              </AbsoluteFill>
            ) : (
              <HomeScreen tap={tap} />
            )}
          </AbsoluteFill>
        </PhoneShell>
        <div style={{marginTop: 18, textAlign: 'center', fontFamily: mono, fontSize: 15, letterSpacing: 2, textTransform: 'uppercase', color: C.wire}}>
          In a drawer at home
        </div>
      </div>

      {/* the wink */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 70,
          textAlign: 'center',
          fontFamily: display,
          fontWeight: 800,
          fontSize: 50,
          color: C.ash,
          opacity: captionIn,
          transform: `translateY(${(1 - captionIn) * 20}px)`,
        }}
      >
        The phone in your drawer did that. <span style={{color: C.burn}}>&gt;_</span>
      </div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const logo = spring({frame, fps, config: {damping: 200}});
  const tag = spring({frame: frame - 15, fps, config: {damping: 200}});
  const meta = spring({frame: frame - 30, fps, config: {damping: 200}});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 44, opacity: fadeInOut(frame, END, 12, 1)}}>
      <Img src={staticFile('wordmark-light.svg')} style={{width: 620, opacity: logo, transform: `scale(${0.9 + 0.1 * logo})`}} />
      <div style={{fontFamily: display, fontWeight: 800, fontSize: 52, color: C.ash, textAlign: 'center', lineHeight: 1.1, opacity: tag, maxWidth: 900}}>
        Give your AI assistant a physical side phone.
      </div>
      <div style={{fontFamily: mono, fontSize: 24, color: C.wire, textAlign: 'center', lineHeight: 1.7, opacity: meta}}>
        Free and open source · Muse + Android
        <br />
        <span style={{color: C.burnSoft, fontSize: 34, fontWeight: 600}}>useburner.si</span>
      </div>
    </AbsoluteFill>
  );
};

export const DrawerClip: React.FC = () => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: C.handset}}>
      <Sequence durationInFrames={INTRO} premountFor={fps}>
        <Intro />
      </Sequence>
      <Sequence from={INTRO} durationInFrames={MAIN} premountFor={fps}>
        <Main />
      </Sequence>
      <Sequence from={INTRO + MAIN} durationInFrames={END} premountFor={fps}>
        <EndCard />
      </Sequence>
    </AbsoluteFill>
  );
};
