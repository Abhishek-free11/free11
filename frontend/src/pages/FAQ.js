import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Accordion, 
  AccordionContent, 
  AccordionItem, 
  AccordionTrigger 
} from '@/components/ui/accordion';
import { Shield, HelpCircle, ArrowLeft, Coins, Gift, Trophy, Scale } from 'lucide-react';
import api from '../utils/api';

const FAQ = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [faqData, setFaqData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFAQ();
  }, []);

  const fetchFAQ = async () => {
    try {
      const response = await api.getFAQ();
      setFaqData(response.data);
    } catch (error) {
      console.error('Error fetching FAQ:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'coins':
        return <Coins className="h-5 w-5 text-yellow-400" />;
      case 'redemption':
      case 'rewards':
        return <Gift className="h-5 w-5 text-green-400" />;
      case 'progression':
        return <Trophy className="h-5 w-5 text-blue-400" />;
      case 'legal':
        return <Scale className="h-5 w-5 text-purple-400" />;
      default:
        return <HelpCircle className="h-5 w-5 text-slate-300" />;
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'coins':
        return 'border-yellow-500/30 bg-yellow-500/5';
      case 'redemption':
      case 'rewards':
        return 'border-green-500/30 bg-green-500/5';
      case 'progression':
        return 'border-blue-500/30 bg-blue-500/5';
      case 'legal':
        return 'border-purple-500/30 bg-purple-500/5';
      default:
        return 'border-slate-700 bg-slate-800/50';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 pb-20 md:pb-0 via-slate-900 to-slate-900">
      {user && <Navbar />}
      
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl" data-testid="faq-page">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate(user ? '/profile' : '/')}
          className="mb-6 text-slate-300 hover:text-white"
          data-testid="faq-back-btn"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to {user ? 'Profile' : 'Home'}
        </Button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2 flex items-center gap-3">
            <HelpCircle className="h-10 w-10 text-yellow-400" />
            Frequently Asked Questions
          </h1>
          <p className="text-slate-300">Everything you need to know about FREE11</p>
        </div>

        {/* Important Disclaimer Banner */}
        <Card className="mb-8 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/30" data-testid="faq-disclaimer-banner">
          <CardContent className="py-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-500/20 rounded-full">
                <Shield className="h-8 w-8 text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-2">Important: About FREE11 Coins</h3>
                <p className="text-slate-300 text-lg leading-relaxed" data-testid="faq-coin-policy">
                  {faqData?.disclaimer || "FREE11 Coins are non-withdrawable reward tokens redeemable only for goods/services. No cash. No betting. Brand-funded rewards."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* FAQ List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-yellow-400 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-slate-300">Loading FAQ...</p>
          </div>
        ) : faqData?.items ? (
          <Card className="bg-slate-800/70 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <HelpCircle className="h-5 w-5 text-yellow-400" />
                Common Questions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="space-y-2" data-testid="faq-accordion">
                {faqData.items.map((item) => (
                  <AccordionItem 
                    key={item.id} 
                    value={item.id}
                    className={`border rounded-lg px-4 ${getCategoryColor(item.category)}`}
                    data-testid={`faq-item-${item.id}`}
                  >
                    <AccordionTrigger className="text-left hover:no-underline py-4">
                      <div className="flex items-center gap-3">
                        {getCategoryIcon(item.category)}
                        <span className="text-white font-medium">{item.question}</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="text-slate-300 pb-4 pl-8">
                      {item.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-slate-800/70 border-slate-700">
            <CardContent className="py-12 text-center">
              <HelpCircle className="h-16 w-16 text-slate-700 mx-auto mb-4" />
              <p className="text-slate-300">Unable to load FAQ. Please try again later.</p>
            </CardContent>
          </Card>
        )}

        {/* Contact Section */}
        <Card className="mt-8 bg-slate-800/70 border-slate-700">
          <CardContent className="py-6">
            <div className="text-center">
              <h3 className="text-lg font-bold text-white mb-2">Still have questions?</h3>
              <p className="text-slate-300 mb-4">
                Our support team is here to help you with any queries.
              </p>
              <Button 
                variant="outline" 
                className="border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10"
                onClick={() => window.open('mailto:support@free11.com', '_blank')}
                data-testid="faq-contact-btn"
              >
                Contact Support
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FAQ;
